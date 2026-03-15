"""Context window & strategy interfaces — mirrors lemura/src/types/context.ts"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from pylemura.types.adapters import ToolCall, ToolResult

TurnRole = Literal["user", "assistant", "tool", "system"]


@dataclass
class Turn:
    role: TurnRole
    content: str
    token_count: int = 0
    turn_index: int = 0
    compressed: bool = False
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


@dataclass
class ContextWindow:
    system_prompt: str
    scratchpad: str
    turns: list[Turn]
    token_count: int
    max_tokens: int
    compression_summary: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class IContextStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def priority(self) -> int: ...

    @abstractmethod
    def should_apply(self, ctx: ContextWindow) -> bool: ...

    @abstractmethod
    async def apply(self, ctx: ContextWindow) -> ContextWindow: ...
