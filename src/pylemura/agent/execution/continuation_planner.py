"""Continuation planner — mirrors lemura/src/agent/execution/ContinuationPlanner.ts"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

StepStatus = Literal["pending", "running", "done", "failed", "skipped"]
PlanStrategy = Literal["sequential", "parallel", "conditional"]

_STATUS_ICONS = {
    "pending":  "⬜",
    "running":  "🔄",
    "done":     "✅",
    "failed":   "❌",
    "skipped":  "⏭️",
}


@dataclass
class StepCondition:
    step: str
    output_contains: str


@dataclass
class ContinuationStep:
    tool_name: str
    description: str
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    depends_on: list[str] = field(default_factory=list)
    status: StepStatus = "pending"
    output_key: Optional[str] = None
    input_mapping: dict[str, str] = field(default_factory=dict)
    condition: Optional[StepCondition] = None
    _output: Optional[str] = field(default=None, repr=False)


@dataclass
class ContinuationPlan:
    steps: list[ContinuationStep]
    strategy: PlanStrategy = "sequential"
    _outputs: dict[str, str] = field(default_factory=dict, repr=False)


class ContinuationPlanner:
    def __init__(self, plan: ContinuationPlan) -> None:
        self._plan = plan

    def get_plan(self) -> ContinuationPlan:
        return self._plan

    def get_plan_status_string(self) -> str:
        lines = ["### Continuation Plan"]
        for step in self._plan.steps:
            icon = _STATUS_ICONS.get(step.status, "?")
            lines.append(f"  {icon} [{step.step_id[:8]}] {step.tool_name}: {step.description}")
        return "\n".join(lines)

    def get_ready_steps(self) -> list[ContinuationStep]:
        ready = []
        for step in self._plan.steps:
            if step.status != "pending":
                continue
            # Check dependencies are done
            deps_met = all(
                self._get_step(dep_id) is not None
                and self._get_step(dep_id).status == "done"
                for dep_id in step.depends_on
            )
            if not deps_met:
                continue
            # Check conditional
            if step.condition:
                ref_step = self._get_step(step.condition.step)
                if ref_step is None or step.condition.output_contains not in (ref_step._output or ""):
                    continue
            ready.append(step)
        return ready

    def is_complete(self) -> bool:
        return all(
            s.status in ("done", "skipped", "failed")
            for s in self._plan.steps
        )

    def mark_step_running(self, step_id: str) -> None:
        step = self._get_step(step_id)
        if step:
            step.status = "running"

    def mark_step_done(self, step_id: str, output: Optional[str] = None) -> None:
        step = self._get_step(step_id)
        if step:
            step.status = "done"
            step._output = output
            if step.output_key and output is not None:
                self._plan._outputs[step.output_key] = output
            # Propagate: nothing to do for done steps

    def mark_step_failed(self, step_id: str) -> None:
        step = self._get_step(step_id)
        if step:
            step.status = "failed"
            self._propagate_skip(step_id)

    def mark_step_skipped(self, step_id: str) -> None:
        step = self._get_step(step_id)
        if step:
            step.status = "skipped"

    def _propagate_skip(self, failed_id: str) -> None:
        for step in self._plan.steps:
            if failed_id in step.depends_on and step.status == "pending":
                step.status = "skipped"
                self._propagate_skip(step.step_id)

    def get_output(self, key: str) -> Optional[str]:
        return self._plan._outputs.get(key)

    def resolve_inputs(
        self,
        step: ContinuationStep,
        base_args: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        args = dict(base_args or {})
        for param, output_key in step.input_mapping.items():
            value = self.get_output(output_key)
            if value is not None:
                args[param] = value
        return args

    def _get_step(self, step_id: str) -> Optional[ContinuationStep]:
        return next((s for s in self._plan.steps if s.step_id == step_id), None)
