"""Summary injection strategy — mirrors lemura/src/context/SummaryInjectionStrategy.ts
Re-injects compression_summary as a synthetic system turn so the model
always sees what was compressed in a prior iteration.
"""
from __future__ import annotations
from dataclasses import dataclass
from pylemura.types.context import ContextWindow, IContextStrategy, Turn

_SUMMARY_MARKER = "__compression_summary__"


@dataclass
class SummaryInjectionStrategyConfig:
    priority: int = 1


class SummaryInjectionStrategy(IContextStrategy):
    def __init__(self, config: SummaryInjectionStrategyConfig | None = None) -> None:
        cfg = config or SummaryInjectionStrategyConfig()
        self._priority = cfg.priority

    @property
    def name(self) -> str:
        return "summary_injection"

    @property
    def priority(self) -> int:
        return self._priority

    def should_apply(self, ctx: ContextWindow) -> bool:
        return bool(ctx.compression_summary)

    async def apply(self, ctx: ContextWindow) -> ContextWindow:
        if not ctx.compression_summary:
            return ctx

        summary_content = (
            f"[Context Summary]\nThe following events occurred earlier in this session "
            f"and have been compressed:\n\n{ctx.compression_summary}"
        )
        summary_turn = Turn(
            role="system",
            content=summary_content,
            token_count=max(1, len(summary_content) // 4),
            compressed=True,
        )

        # Replace existing summary turn if present (idempotent)
        filtered = [t for t in ctx.turns if t.role != "system" or _SUMMARY_MARKER not in t.content]
        summary_turn.content = summary_content + f"\n<!-- {_SUMMARY_MARKER} -->"

        ctx.turns = [summary_turn] + [t for t in filtered if t.role != "system" or "compression_summary" not in str(t.content)]
        return ctx
