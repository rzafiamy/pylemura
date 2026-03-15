"""Tool definition interfaces — mirrors lemura/src/types/tools.ts"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Literal, Optional

if TYPE_CHECKING:
    from pylemura.types.logger import ILogger
    from pylemura.types.rag import IRAGAdapter
    from pylemura.types.adapters import IProviderAdapter
    from pylemura.context.short_term_memory_registry import ShortTermMemoryRegistry
    from pylemura.types.storage import IScratchpadAdapter


@dataclass
class ToolContext:
    session_id: str
    turn_index: int
    logger: "ILogger"
    adapter: Optional["IProviderAdapter"] = None
    rag_adapter: Optional["IRAGAdapter"] = None
    stm_registry: Optional["ShortTermMemoryRegistry"] = None
    scratchpad: str = ""
    scratchpad_adapter: Optional["IScratchpadAdapter"] = None


ToolExecuteFunc = Callable[[Any, ToolContext], Coroutine[Any, Any, Any]]

ToolDecision = Literal["accept", "deny", "ask"]


@dataclass
class ToolFirewallRule:
    decision: ToolDecision
    name: Optional[str] = None       # regex pattern for tool name
    arguments: Optional[str] = None  # regex pattern for args JSON
    reason: Optional[str] = None


@dataclass
class ToolFirewallConfig:
    default_decision: ToolDecision = "ask"
    rules: list[ToolFirewallRule] = field(default_factory=list)
    on_ask: Optional[Callable[[str, str], Coroutine[Any, Any, ToolDecision]]] = None


@dataclass
class ToolFirewallResult:
    decision: ToolDecision
    reason: Optional[str] = None


@dataclass
class ToolExecutionBudget:
    max_calls_per_tool: Optional[dict[str, int]] = None  # tool_name -> max calls
    max_total_calls: Optional[int] = None


class IToolResponseProcessor(ABC):
    @abstractmethod
    def evaluate(self, response: str, tool_name: str, context: ToolContext) -> dict[str, Any]: ...

    @abstractmethod
    def compress(self, response: str, evaluation: dict[str, Any]) -> str: ...


class IToolDefinition(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]: ...

    @abstractmethod
    async def execute(self, params: Any, context: ToolContext) -> Any: ...


class FunctionTool(IToolDefinition):
    """Convenience wrapper to create a tool from a plain async function."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        func: ToolExecuteFunc,
    ) -> None:
        self._name = name
        self._description = description
        self._parameters = parameters
        self._func = func

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, params: Any, context: ToolContext) -> Any:
        return await self._func(params, context)
