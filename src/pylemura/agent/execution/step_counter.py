"""Step counter — mirrors lemura/src/agent/execution/StepCounter.ts"""
from __future__ import annotations
from typing import Optional


class StepCounter:
    def __init__(self, max_steps: Optional[int] = None) -> None:
        self._count = 0
        self._max = max_steps

    def increment(self) -> None:
        self._count += 1

    def is_max_reached(self) -> bool:
        if self._max is None:
            return False
        return self._count >= self._max

    @property
    def count(self) -> int:
        return self._count

    @property
    def max_steps(self) -> Optional[int]:
        return self._max

    def reset(self) -> None:
        self._count = 0
