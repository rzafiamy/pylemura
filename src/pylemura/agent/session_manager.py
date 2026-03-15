"""SessionManager — main ReAct loop orchestrator.
Mirrors lemura/src/agent/SessionManager.ts
"""
from __future__ import annotations
import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Optional

from pylemura.agent.execution.continuation_planner import ContinuationPlan, ContinuationPlanner
from pylemura.agent.execution.final_response_formatter import FinalResponseFormatter
from pylemura.agent.execution.goal_injector import Goal, GoalInjector
from pylemura.agent.execution.step_counter import StepCounter
from pylemura.agent.execution.tool_response_processor import ToolResponseProcessor
from pylemura.context.context_manager import ContextManager
from pylemura.logger.default_logger import DefaultLogger
from pylemura.mcp.mcp_client_registry import MCPClientRegistry
from pylemura.media.media_bridge import MediaBridge
from pylemura.skills.skill_injector import SkillInjector
from pylemura.tools.tool_firewall import evaluate_tool_firewall
from pylemura.tools.tool_registry import ToolRegistry
from pylemura.types.adapters import (
    CompletionChunk,
    CompletionRequest,
    NormalizedMessage,
    ToolCall,
)
from pylemura.types.agent import SessionConfig, TraceEvent
from pylemura.types.context import ContextWindow, Turn
from pylemura.types.errors import LemuraMaxIterationsError
from pylemura.types.tools import ToolContext


class SessionManager:
    def __init__(self, config: SessionConfig) -> None:
        self._cfg = config
        self._session_id = str(uuid.uuid4())
        self._logger = config.logger or DefaultLogger()
        self._adapter = config.adapter

        # Core subsystems
        self._context_manager = ContextManager()
        for strategy in config.compression_strategies:
            self._context_manager.register_strategy(strategy)

        self._tool_registry = ToolRegistry()
        for tool in config.tools:
            self._tool_registry.register(tool)

        self._skill_injector = SkillInjector(estimate_tokens=self._adapter.estimate_tokens)
        for skill in config.skills:
            self._skill_injector.register(skill)
        # Enable dynamic skills/tags from config
        for name in config.active_dynamic_skills:
            self._skill_injector.enable_skill(name)
        if config.active_dynamic_tags:
            self._skill_injector.enable_by_tags(config.active_dynamic_tags)

        # Context window
        self._context = ContextWindow(
            system_prompt=config.system_prompt,
            scratchpad="",
            turns=[],
            token_count=0,
            max_tokens=config.max_tokens,
        )

        # Execution helpers
        self._step_counter = StepCounter(max_steps=config.max_steps)
        self._goal_injector: Optional[GoalInjector] = None
        self._continuation_planner: Optional[ContinuationPlanner] = None
        self._response_processor = (
            config.tool_response_processor or ToolResponseProcessor()
        )
        self._iterations = 0

        # MCP
        self._mcp_registry: Optional[MCPClientRegistry] = None
        self._mcp_ready: Optional[asyncio.Task] = None
        if config.mcp_servers:
            self._mcp_registry = MCPClientRegistry(self._logger)
            self._mcp_ready = asyncio.ensure_future(self._init_mcp())

        # Media
        self._media = MediaBridge(self._adapter)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_context(self) -> ContextWindow:
        return self._context

    def get_history(self) -> list[Turn]:
        return list(self._context.turns)

    def load_history(self, history: list[dict[str, Any]]) -> None:
        """Restore turns from a serialized history list."""
        for entry in history:
            self._context.turns.append(
                Turn(
                    role=entry.get("role", "user"),
                    content=entry.get("content", ""),
                    token_count=entry.get("token_count", 0),
                    turn_index=entry.get("turn_index", 0),
                    compressed=entry.get("compressed", False),
                )
            )

    def get_media(self) -> MediaBridge:
        return self._media

    @property
    def tools(self) -> ToolRegistry:
        return self._tool_registry

    @property
    def skills(self) -> SkillInjector:
        return self._skill_injector

    def set_goal(self, goal: Goal) -> None:
        self._goal_injector = GoalInjector(goal)

    def set_plan(
        self,
        steps: list[Any],
        strategy: str = "sequential",
    ) -> None:
        plan = ContinuationPlan(steps=steps, strategy=strategy)
        self._continuation_planner = ContinuationPlanner(plan)

    # ------------------------------------------------------------------
    # Main entry points
    # ------------------------------------------------------------------

    async def run(self, user_message: str) -> str:
        await self._ensure_ready()
        await self._load_scratchpad()
        self._add_user_turn(user_message)
        self._trace("session_start", "run", {"user_message": user_message[:100]})

        if self._cfg.enable_goal_planning and self._goal_injector is None:
            await self._plan_goal(user_message)

        result = await self._react_loop()
        self._trace("session_end", "run", {"response": result[:100]})
        return result

    async def stream(self, user_message: str) -> AsyncIterator[CompletionChunk]:
        await self._ensure_ready()
        await self._load_scratchpad()
        self._add_user_turn(user_message)
        self._trace("session_start", "stream", {"user_message": user_message[:100]})

        async for chunk in self._react_loop_stream():
            yield chunk

    async def reset(self) -> None:
        self._context.turns.clear()
        self._context.token_count = 0
        self._context.compression_summary = None
        self._step_counter.reset()
        self._iterations = 0
        self._goal_injector = None
        self._continuation_planner = None

    async def close(self) -> None:
        if self._mcp_registry:
            await self._mcp_registry.disconnect_all()

    # ------------------------------------------------------------------
    # ReAct loop
    # ------------------------------------------------------------------

    async def _react_loop(self) -> str:
        while True:
            self._iterations += 1
            max_iter = self._cfg.max_iterations
            if max_iter is not None and self._iterations > max_iter:
                raise LemuraMaxIterationsError(max_iter)

            self._trace("iteration_start", f"iteration_{self._iterations}", {})

            # Prepare context (apply compression strategies)
            compression_occurred = False
            prev_turn_count = len(self._context.turns)
            self._context = await self._context_manager.prepare(self._context)
            if len(self._context.turns) < prev_turn_count:
                compression_occurred = True
                self._trace("compression", "context_compressed", {})

            # Build messages to send
            messages = self._build_messages(compression_occurred)

            # LLM call
            request = CompletionRequest(
                model=self._cfg.model,
                messages=messages,
                tools=self._tool_registry.get_schemas(),
                max_tokens=self._cfg.max_completion_tokens,
            )

            response = await self._adapter.complete(request)
            self._trace("iteration_end", f"iteration_{self._iterations}", {
                "finish_reason": response.finish_reason,
                "tool_calls": len(response.tool_calls),
            })

            # No tool calls → final response
            if not response.tool_calls or response.finish_reason == "stop":
                # Append assistant turn
                self._context.turns.append(Turn(
                    role="assistant",
                    content=response.content,
                    token_count=max(1, len(response.content) // 4),
                    turn_index=len(self._context.turns),
                ))
                if self._cfg.on_turn:
                    self._cfg.on_turn({"role": "assistant", "content": response.content})
                return FinalResponseFormatter.format(response.content)

            # Process tool calls
            if self._step_counter.is_max_reached():
                # Force conclusion
                self._context.turns.append(Turn(
                    role="assistant",
                    content=response.content or "I have reached my tool call limit.",
                    token_count=max(1, len(response.content or "") // 4),
                    turn_index=len(self._context.turns),
                ))
                return FinalResponseFormatter.format(response.content or "I have reached my tool call limit.")

            # Add assistant turn with tool calls
            assistant_turn = Turn(
                role="assistant",
                content=response.content or "",
                token_count=max(1, len(response.content or "") // 4),
                turn_index=len(self._context.turns),
                tool_calls=response.tool_calls,
            )
            self._context.turns.append(assistant_turn)

            # Execute tools
            await self._execute_tool_calls(response.tool_calls)
            self._step_counter.increment()

            # Update goal if applicable
            if self._goal_injector:
                self._goal_injector.increment_turn()

    async def _react_loop_stream(self) -> AsyncIterator[CompletionChunk]:
        """Streaming variant: yields chunks until final response is assembled."""
        while True:
            self._iterations += 1
            max_iter = self._cfg.max_iterations
            if max_iter is not None and self._iterations > max_iter:
                raise LemuraMaxIterationsError(max_iter)

            compression_occurred = False
            prev_turn_count = len(self._context.turns)
            self._context = await self._context_manager.prepare(self._context)
            if len(self._context.turns) < prev_turn_count:
                compression_occurred = True

            messages = self._build_messages(compression_occurred)
            request = CompletionRequest(
                model=self._cfg.model,
                messages=messages,
                tools=self._tool_registry.get_schemas(),
                max_tokens=self._cfg.max_completion_tokens,
                stream=True,
            )

            # Collect streamed response
            full_content = ""
            tool_call_acc: dict[int, dict[str, Any]] = {}
            finish_reason: Optional[str] = None

            async for chunk in self._adapter.stream(request):
                full_content += chunk.delta
                if chunk.tool_call_delta:
                    idx = chunk.tool_call_delta.get("index", 0)
                    if idx not in tool_call_acc:
                        tool_call_acc[idx] = {"id": "", "name": "", "arguments": ""}
                    delta = chunk.tool_call_delta.get("delta", {})
                    fn = delta.get("function", {})
                    if delta.get("id"):
                        tool_call_acc[idx]["id"] = delta["id"]
                    if fn.get("name"):
                        tool_call_acc[idx]["name"] += fn["name"]
                    if fn.get("arguments"):
                        tool_call_acc[idx]["arguments"] += fn["arguments"]
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                yield chunk

            # Reconstruct tool calls from accumulated deltas
            tool_calls = [
                ToolCall(id=v["id"], name=v["name"], arguments=v["arguments"])
                for v in tool_call_acc.values()
                if v.get("name")
            ]

            if not tool_calls or finish_reason == "stop":
                self._context.turns.append(Turn(
                    role="assistant",
                    content=full_content,
                    token_count=max(1, len(full_content) // 4),
                    turn_index=len(self._context.turns),
                ))
                return

            if self._step_counter.is_max_reached():
                return

            assistant_turn = Turn(
                role="assistant",
                content=full_content,
                token_count=max(1, len(full_content) // 4),
                turn_index=len(self._context.turns),
                tool_calls=tool_calls,
            )
            self._context.turns.append(assistant_turn)
            await self._execute_tool_calls(tool_calls)
            self._step_counter.increment()

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    async def _execute_tool_calls(self, tool_calls: list[ToolCall]) -> None:
        context = ToolContext(
            session_id=self._session_id,
            turn_index=len(self._context.turns),
            logger=self._logger,
            adapter=self._adapter,
            rag_adapter=self._cfg.rag_adapter,
            stm_registry=self._cfg.stm_registry,
            scratchpad=self._context.scratchpad,
            scratchpad_adapter=self._cfg.scratchpad_adapter,
        )

        if self._cfg.parallel_tool_calls and len(tool_calls) > 1:
            calls = [{"id": tc.id, "name": tc.name, "params": self._parse_args(tc.arguments)} for tc in tool_calls]
            results = await self._tool_registry.execute_parallel(calls, context)
            for item in results:
                content = self._format_tool_result(item)
                self._append_tool_result(item["id"], content)
        else:
            for tc in tool_calls:
                content = await self._run_single_tool(tc, context)
                self._append_tool_result(tc.id, content)

    async def _run_single_tool(self, tc: ToolCall, context: ToolContext) -> str:
        tool_name = tc.name
        args_json = tc.arguments
        args = self._parse_args(args_json)

        self._trace("tool_call", tool_name, {"args": args_json[:200]})
        self._logger.debug(f"[Tool] Calling '{tool_name}'", {"args": args_json[:100]})

        # Firewall check
        if self._cfg.tool_firewall:
            result = evaluate_tool_firewall(self._cfg.tool_firewall, tool_name, args_json, self._logger)
            if result.decision == "deny":
                return f"Tool call denied: {result.reason or 'Firewall rule'}"
            if result.decision == "ask" and self._cfg.tool_firewall.on_ask:
                decision = await self._cfg.tool_firewall.on_ask(tool_name, args_json)
                if decision == "deny":
                    return f"Tool call denied by user"

        # Budget check
        if self._cfg.tool_execution_budget:
            budget = self._cfg.tool_execution_budget
            if budget.max_calls_per_tool and tool_name in budget.max_calls_per_tool:
                if self._tool_registry.get_call_count(tool_name) >= budget.max_calls_per_tool[tool_name]:
                    return f"Tool '{tool_name}' call budget exhausted"
            if budget.max_total_calls is not None:
                total = sum(self._tool_registry.get_call_count(t.name) for t in self._tool_registry.get_all())
                if total >= budget.max_total_calls:
                    return "Total tool call budget exhausted"

        try:
            raw_result = await self._tool_registry.execute(tool_name, args, context)
            result_str = str(raw_result) if not isinstance(raw_result, str) else raw_result
            self._trace("tool_result", tool_name, {"result": result_str[:200]})

            # Evaluate & compress if needed
            evaluation = self._response_processor.evaluate(result_str, tool_name, context)
            if evaluation.get("should_compress"):
                result_str = self._response_processor.compress(result_str, evaluation)

            # Token budget
            if self._cfg.max_tokens_per_tool:
                max_chars = self._cfg.max_tokens_per_tool * 4
                if len(result_str) > max_chars:
                    result_str = result_str[:max_chars] + f"\n[Truncated to {self._cfg.max_tokens_per_tool} tokens]"

            return result_str
        except Exception as e:
            self._logger.error(f"[Tool] '{tool_name}' error: {e}")
            return f"Error: {e}"

    def _format_tool_result(self, item: dict[str, Any]) -> str:
        if "error" in item:
            return f"Error: {item['error']}"
        raw = item.get("result", "")
        return str(raw) if not isinstance(raw, str) else raw

    def _append_tool_result(self, tool_call_id: str, content: str) -> None:
        turn = Turn(
            role="tool",
            content=content,
            token_count=max(1, len(content) // 4),
            turn_index=len(self._context.turns),
        )
        self._context.turns.append(turn)

    # ------------------------------------------------------------------
    # Message building
    # ------------------------------------------------------------------

    def _build_messages(self, compression_occurred: bool = False) -> list[NormalizedMessage]:
        messages: list[NormalizedMessage] = []

        # System prompt + skill injections
        system_content = self._context.system_prompt
        system_skills = self._skill_injector.build_injection_block("system_prompt")
        if system_skills:
            system_content = f"{system_content}\n\n{system_skills}".strip()

        if self._goal_injector and self._cfg.goal_injection_position == "system_prompt":
            if self._goal_injector.should_inject_this_turn(self._iterations, compression_occurred, self._cfg.goal_injection_n):
                system_content = self._goal_injector.inject_into(system_content)

        if self._continuation_planner:
            system_content += f"\n\n{self._continuation_planner.get_plan_status_string()}"

        if system_content:
            messages.append(NormalizedMessage(role="system", content=system_content))

        # History turns
        for turn in self._context.turns:
            if turn.role == "system":
                # Already included above or from compression
                messages.append(NormalizedMessage(role="system", content=turn.content))
            elif turn.role == "assistant":
                msg = NormalizedMessage(role="assistant", content=turn.content)
                if turn.tool_calls:
                    msg.tool_calls = turn.tool_calls
                messages.append(msg)
            elif turn.role == "tool":
                # Find the tool_call_id from the previous assistant turn
                tc_id = self._find_tool_call_id_for_turn(turn)
                messages.append(NormalizedMessage(
                    role="tool",
                    content=turn.content,
                    tool_call_id=tc_id or "unknown",
                ))
            else:
                # user or other
                msg_content = turn.content
                # Inject pre_turn skills before last user message
                if turn.role == "user" and turn == self._context.turns[-1]:
                    pre_turn_skills = self._skill_injector.build_injection_block("pre_turn")
                    if pre_turn_skills:
                        msg_content = f"{pre_turn_skills}\n\n{msg_content}"
                    if self._goal_injector and self._cfg.goal_injection_position == "pre_turn":
                        if self._goal_injector.should_inject_this_turn(self._iterations, False, self._cfg.goal_injection_n):
                            msg_content = self._goal_injector.inject_into(msg_content)
                messages.append(NormalizedMessage(role=turn.role, content=msg_content))

        return messages

    def _find_tool_call_id_for_turn(self, tool_turn: Turn) -> Optional[str]:
        """Find the tool_call_id by looking at the preceding assistant tool_calls."""
        tool_index = 0
        for i, t in enumerate(self._context.turns):
            if t == tool_turn:
                break
        # Count tool turns between this and the preceding assistant turn
        j = tool_index
        for idx in range(len(self._context.turns)):
            if self._context.turns[idx] == tool_turn:
                j = idx
                break
        for idx in range(j - 1, -1, -1):
            t = self._context.turns[idx]
            if t.role == "assistant" and t.tool_calls:
                # Count preceding tool turns since this assistant turn
                tool_turn_count = sum(
                    1 for k in range(idx + 1, j)
                    if self._context.turns[k].role == "tool"
                )
                if tool_turn_count < len(t.tool_calls):
                    return t.tool_calls[tool_turn_count].id
                break
        return None

    # ------------------------------------------------------------------
    # Goal planning
    # ------------------------------------------------------------------

    async def _plan_goal(self, user_message: str) -> None:
        prompt = (
            f"Decompose this user request into 3-5 concrete sub-goals and "
            f"list 2-3 success criteria. Respond as JSON:\n"
            f"{{\"decomposition\": [...], \"success_criteria\": [...]}}\n\n"
            f"Request: {user_message}"
        )
        try:
            resp = await self._adapter.complete(CompletionRequest(
                model=self._cfg.model,
                messages=[NormalizedMessage(role="user", content=prompt)],
                max_tokens=400,
            ))
            # Extract JSON from response
            content = resp.content.strip()
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                goal = Goal(
                    statement=user_message,
                    decomposition=data.get("decomposition", []),
                    success_criteria=data.get("success_criteria", []),
                    injection_frequency=self._cfg.goal_injection_frequency,
                    injection_position=self._cfg.goal_injection_position,
                )
                self._goal_injector = GoalInjector(goal)
                self._logger.debug("[Goal] Planned sub-goals", {"count": len(goal.decomposition)})
        except Exception as e:
            self._logger.warn(f"[Goal] Goal planning failed: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _ensure_ready(self) -> None:
        if self._mcp_ready is not None:
            await self._mcp_ready
            self._mcp_ready = None

    async def _init_mcp(self) -> None:
        if self._mcp_registry is None:
            return
        for server in self._cfg.mcp_servers:
            await self._mcp_registry.register(server.name, server)
        await self._mcp_registry.connect_all()
        mcp_tools = await self._mcp_registry.discover_tools()
        for tool in mcp_tools:
            self._tool_registry.register(tool)
        self._logger.info(f"[MCP] Loaded {len(mcp_tools)} tools from MCP servers")

    async def _load_scratchpad(self) -> None:
        if self._cfg.scratchpad_adapter:
            self._context.scratchpad = await self._cfg.scratchpad_adapter.load(self._session_id)

    def _add_user_turn(self, message: str) -> None:
        turn = Turn(
            role="user",
            content=message,
            token_count=max(1, len(message) // 4),
            turn_index=len(self._context.turns),
        )
        self._context.turns.append(turn)
        if self._cfg.on_turn:
            self._cfg.on_turn({"role": "user", "content": message})

    @staticmethod
    def _parse_args(arguments: str) -> Any:
        if not arguments:
            return {}
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return {}

    def _trace(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        if self._cfg.on_trace:
            self._cfg.on_trace(TraceEvent(type=event_type, name=name, data=data))  # type: ignore[arg-type]
