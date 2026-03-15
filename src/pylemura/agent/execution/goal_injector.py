"""Goal injector — mirrors lemura/src/agent/execution/GoalInjector.ts"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Literal, Optional


GoalInjectionFrequency = Literal["always", "every_N_turns", "on_compression"]
GoalInjectionPosition = Literal["system_prompt", "pre_turn"]


@dataclass
class Goal:
    statement: str
    decomposition: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    injection_frequency: GoalInjectionFrequency = "always"
    injection_position: GoalInjectionPosition = "pre_turn"
    completed_sub_goals: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class GoalInjector:
    def __init__(self, goal: Goal) -> None:
        self._goal = goal
        self._turn_index = 0

    def get_formatted_block(self) -> str:
        lines = [f"## Current Goal\n{self._goal.statement}"]
        if self._goal.decomposition:
            lines.append("\n### Sub-goals")
            for sg in self._goal.decomposition:
                done = sg in self._goal.completed_sub_goals
                prefix = "[x]" if done else "[ ]"
                lines.append(f"  {prefix} {sg}")
        if self._goal.success_criteria:
            lines.append("\n### Success Criteria")
            for sc in self._goal.success_criteria:
                lines.append(f"  - {sc}")
        return "\n".join(lines)

    def inject_into(self, prompt: str) -> str:
        block = self.get_formatted_block()
        return f"{block}\n\n{prompt}"

    def should_inject_this_turn(
        self,
        turn_index: int,
        compression_occurred: bool,
        injection_n: int = 3,
    ) -> bool:
        freq = self._goal.injection_frequency
        if freq == "always":
            return True
        if freq == "on_compression":
            return compression_occurred
        if freq == "every_N_turns":
            return turn_index % injection_n == 0
        return False

    def update_decomposition(
        self,
        decomposition: list[str],
        success_criteria: Optional[list[str]] = None,
    ) -> None:
        self._goal.decomposition = decomposition
        if success_criteria is not None:
            self._goal.success_criteria = success_criteria

    def mark_sub_goal_done(self, sub_goal: str) -> None:
        if sub_goal not in self._goal.completed_sub_goals:
            self._goal.completed_sub_goals.append(sub_goal)

    def get_goal(self) -> Goal:
        return self._goal

    def increment_turn(self) -> None:
        self._turn_index += 1
