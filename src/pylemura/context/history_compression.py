"""History (sliding window) compression — mirrors lemura/src/context/HistoryCompressionStrategy.ts"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from pylemura.types.adapters import CompletionRequest, IProviderAdapter, NormalizedMessage
from pylemura.types.context import ContextWindow, IContextStrategy, Turn


@dataclass
class HistoryCompressionConfig:
    keep_last_n: int = 6
    trigger_ratio: float = 0.85
    priority: int = 30
    summary_max_tokens: int = 400
    summary_model: Optional[str] = None


class HistoryCompressionStrategy(IContextStrategy):
    def __init__(
        self,
        adapter: IProviderAdapter,
        config: Optional[HistoryCompressionConfig] = None,
    ) -> None:
        self._adapter = adapter
        self._cfg = config or HistoryCompressionConfig()

    @property
    def name(self) -> str:
        return "history_compression"

    @property
    def priority(self) -> int:
        return self._cfg.priority

    def should_apply(self, ctx: ContextWindow) -> bool:
        if ctx.max_tokens == 0:
            return False
        ratio = ctx.token_count / ctx.max_tokens
        return ratio >= self._cfg.trigger_ratio and len(ctx.turns) > self._cfg.keep_last_n

    async def apply(self, ctx: ContextWindow) -> ContextWindow:
        turns = ctx.turns
        keep = turns[-self._cfg.keep_last_n :]
        removed = turns[: -self._cfg.keep_last_n]

        if not removed:
            return ctx

        removed_text = "\n".join(f"[{t.role}]: {t.content}" for t in removed)
        prompt = (
            "Summarize the following conversation history into a single paragraph:\n\n"
            + removed_text
        )

        try:
            resp = await self._adapter.complete(
                CompletionRequest(
                    model=self._cfg.summary_model or "gpt-4o-mini",
                    messages=[NormalizedMessage(role="user", content=prompt)],
                    max_tokens=self._cfg.summary_max_tokens,
                )
            )
            summary = resp.content.strip()
        except Exception:
            summary = removed_text[:800] + ("..." if len(removed_text) > 800 else "")

        ctx.turns = keep
        ctx.compression_summary = (
            (ctx.compression_summary + "\n\n" if ctx.compression_summary else "") + summary
        )
        return ctx
