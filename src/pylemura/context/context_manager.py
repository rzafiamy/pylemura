"""Context manager — orchestrates compression strategies.
Mirrors lemura/src/context/ContextManager.ts
"""
from __future__ import annotations
from pylemura.types.context import ContextWindow, IContextStrategy
from pylemura.types.errors import LemuraContextOverflowError


class ContextManager:
    def __init__(self) -> None:
        self._strategies: list[IContextStrategy] = []

    def register_strategy(self, strategy: IContextStrategy) -> None:
        self._strategies.append(strategy)
        self._strategies.sort(key=lambda s: s.priority)

    async def prepare(
        self,
        context: ContextWindow,
        safety_margin: float = 0.95,
    ) -> ContextWindow:
        effective_max = int(context.max_tokens * safety_margin)
        ctx = context

        for strategy in self._strategies:
            ctx = _recalculate_token_count(ctx)
            if strategy.should_apply(ctx):
                ctx = await strategy.apply(ctx)

        ctx = _recalculate_token_count(ctx)
        if ctx.token_count > effective_max:
            raise LemuraContextOverflowError(
                f"Context ({ctx.token_count} tokens) exceeds max ({effective_max}) after all strategies"
            )
        return ctx


def _recalculate_token_count(ctx: ContextWindow) -> ContextWindow:
    from pylemura.types.adapters import IProviderAdapter
    total = max(1, len(ctx.system_prompt) // 4)
    for turn in ctx.turns:
        if turn.token_count == 0:
            turn.token_count = max(1, len(str(turn.content)) // 4)
        total += turn.token_count
    ctx.token_count = total
    return ctx
