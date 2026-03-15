"""Agent session configuration — mirrors lemura/src/types/agent.ts"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal, Optional, Union

from pylemura.types.adapters import IProviderAdapter
from pylemura.types.context import IContextStrategy
from pylemura.types.logger import ILogger
from pylemura.types.mcp import MCPServerConfig
from pylemura.types.rag import IRAGAdapter
from pylemura.types.skills import ISkill
from pylemura.types.storage import IScratchpadAdapter
from pylemura.types.tools import (
    IToolDefinition,
    IToolResponseProcessor,
    ToolExecutionBudget,
    ToolFirewallConfig,
)

GoalInjectionFrequency = Literal["always", "every_N_turns", "on_compression"]
GoalInjectionPosition = Literal["system_prompt", "pre_turn"]
ContinuationStrategy = Literal["sequential", "parallel", "conditional"]
TraceEventType = Literal[
    "tool_call",
    "tool_result",
    "iteration_start",
    "iteration_end",
    "compression",
    "goal_inject",
    "plan_update",
    "stream_chunk",
    "session_start",
    "session_end",
]


@dataclass
class TraceEvent:
    type: TraceEventType
    name: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaConfig:
    enable_transcription: bool = False
    enable_synthesis: bool = False
    enable_vision: bool = False
    enable_image_gen: bool = False


@dataclass
class SessionConfig:
    adapter: IProviderAdapter
    model: str
    max_tokens: int

    # Execution control
    max_iterations: Optional[int] = None
    max_steps: int = 20
    max_completion_tokens: int = 2000
    parallel_tool_calls: bool = False

    # Tools & Skills
    tools: list[IToolDefinition] = field(default_factory=list)
    skills: list[ISkill] = field(default_factory=list)
    active_dynamic_skills: list[str] = field(default_factory=list)
    active_dynamic_tags: list[str] = field(default_factory=list)

    # Context & Compression
    compression_strategies: list[IContextStrategy] = field(default_factory=list)
    system_prompt: str = ""

    # Advanced execution
    enable_goal_planning: bool = False
    goal_injection_frequency: GoalInjectionFrequency = "always"
    goal_injection_position: GoalInjectionPosition = "pre_turn"
    goal_injection_n: int = 3

    enable_continuation_planning: bool = False
    continuation_strategy: ContinuationStrategy = "sequential"

    # Tool execution constraints
    tool_execution_budget: Optional[ToolExecutionBudget] = None
    tool_firewall: Optional[ToolFirewallConfig] = None
    tool_response_processor: Optional[IToolResponseProcessor] = None
    tool_response_token_budget: int = 2000
    max_tokens_per_tool: Optional[int] = None

    # Memory & Storage
    stm_registry: Optional[Any] = None           # ShortTermMemoryRegistry
    scratchpad_adapter: Optional[IScratchpadAdapter] = None

    # RAG
    rag_adapter: Optional[IRAGAdapter] = None

    # Media
    media: Optional[MediaConfig] = None

    # MCP Servers
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)

    # Callbacks & Logging
    logger: Optional[ILogger] = None
    on_turn: Optional[Callable[[Any], None]] = None
    on_trace: Optional[Callable[[TraceEvent], None]] = None
