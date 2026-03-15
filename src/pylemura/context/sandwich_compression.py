"""Sandwich compression strategy — mirrors lemura/src/context/SandwichCompressionStrategy.ts
Preserves first N + last M turns, summarizes the middle via LLM.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from pylemura.types.adapters import CompletionRequest, IProviderAdapter, NormalizedMessage
from pylemura.types.context import ContextWindow, IContextStrategy, Turn


@dataclass
class SandwichCompressionConfig:
    preserve_first: int = 2
    preserve_last: int = 4
    trigger_ratio: float = 0.80
    priority: int = 20
    summary_max_tokens: int = 500
    summary_model: Optional[str] = None


class SandwichCompressionStrategy(IContextStrategy):
    def __init__(
        self,
        adapter: IProviderAdapter,
        config: Optional[SandwichCompressionConfig] = None,
    ) -> None:
        self._adapter = adapter
        self._cfg = config or SandwichCompressionConfig()

    @property
    def name(self) -> str:
        return "sandwich_compression"

    @property
    def priority(self) -> int:
        return self._cfg.priority

    def should_apply(self, ctx: ContextWindow) -> bool:
        if ctx.max_tokens == 0:
            return False
        ratio = ctx.token_count / ctx.max_tokens
        total = len(ctx.turns)
        min_turns = self._cfg.preserve_first + self._cfg.preserve_last + 1
        return ratio >= self._cfg.trigger_ratio and total >= min_turns

    async def apply(self, ctx: ContextWindow) -> ContextWindow:
        turns = ctx.turns
        first = turns[: self._cfg.preserve_first]
        last = turns[-self._cfg.preserve_last :] if self._cfg.preserve_last else []
        middle = turns[self._cfg.preserve_first : len(turns) - self._cfg.preserve_last if self._cfg.preserve_last else len(turns)]

        if not middle:
            return ctx

        # Build summary of middle turns
        middle_text = "\n".join(
            f"[{t.role}]: {t.content}" for t in middle
        )
        summary_prompt = (
            "Summarize the following conversation history concisely, "
            "preserving all important facts, decisions, and context:\n\n"
            + middle_text
        )

        try:
            resp = await self._adapter.complete(
                CompletionRequest(
                    model=self._cfg.summary_model or "gpt-4o-mini",
                    messages=[
                        NormalizedMessage(role="user", content=summary_prompt)
                    ],
                    max_tokens=self._cfg.summary_max_tokens,
                )
            )
            summary = resp.content.strip()
        except Exception:
            # Fallback: use truncated middle text
            summary = middle_text[:1000] + ("..." if len(middle_text) > 1000 else "")

        # Build compressed placeholder turn
        compressed_content = f"[Compressed: {len(middle)} turns summarized]\n{summary}"
        compressed_turn = Turn(
            role="system",
            content=compressed_content,
            token_count=max(1, len(compressed_content) // 4),
            compressed=True,
        )

        ctx.turns = first + [compressed_turn] + last
        ctx.compression_summary = (
            (ctx.compression_summary + "\n\n---\n\n" if ctx.compression_summary else "") + summary
        )
        return ctx
