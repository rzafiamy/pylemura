"""Unit tests for ContinuationPlanner v1.4.4 additions."""
import pytest
from pylemura.agent.execution.continuation_planner import (
    ContinuationPlan,
    ContinuationPlanner,
    ContinuationStep,
    StepVerifier,
    StepVerifierResult,
)


def make_planner(*steps, **kwargs):
    plan = ContinuationPlan(steps=list(steps))
    return ContinuationPlanner(plan, **kwargs)


# ---------------------------------------------------------------------------
# StepVerifierResult
# ---------------------------------------------------------------------------

def test_step_verifier_result_pass():
    r = StepVerifierResult(status="pass")
    assert r.status == "pass"
    assert r.reason is None


def test_step_verifier_result_retry_with_reason():
    r = StepVerifierResult(status="retry", reason="Empty result set")
    assert r.status == "retry"
    assert r.reason == "Empty result set"


def test_step_verifier_result_fail():
    r = StepVerifierResult(status="fail", reason="bad output")
    assert r.status == "fail"


# ---------------------------------------------------------------------------
# StepVerifier attached to ContinuationStep
# ---------------------------------------------------------------------------

def test_continuation_step_verify_field_defaults_none():
    s = ContinuationStep(tool_name="t", description="d")
    assert s.verify is None


def test_continuation_step_accepts_verifier():
    verifier = StepVerifier(check=lambda out, args: StepVerifierResult(status="pass"))
    s = ContinuationStep(tool_name="t", description="d", verify=verifier)
    assert s.verify is verifier
    assert s.verify.max_retries == 0


def test_step_verifier_max_retries_custom():
    verifier = StepVerifier(check=lambda o, a: StepVerifierResult(status="pass"), max_retries=3)
    assert verifier.max_retries == 3


# ---------------------------------------------------------------------------
# mark_step_pending / get_retry_count
# ---------------------------------------------------------------------------

def test_mark_step_pending_resets_to_pending():
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s)
    planner.mark_step_running(s.step_id)
    assert planner.get_plan().steps[0].status == "running"
    planner.mark_step_pending(s.step_id)
    assert planner.get_plan().steps[0].status == "pending"


def test_get_retry_count_starts_at_zero():
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s)
    assert planner.get_retry_count(s.step_id) == 0


def test_get_retry_count_increments_on_each_pending():
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s)
    planner.mark_step_pending(s.step_id)
    assert planner.get_retry_count(s.step_id) == 1
    planner.mark_step_pending(s.step_id)
    assert planner.get_retry_count(s.step_id) == 2


def test_get_retry_count_unknown_step_returns_zero():
    planner = make_planner()
    assert planner.get_retry_count("nonexistent") == 0


# ---------------------------------------------------------------------------
# mark_step_failed with reason and callback
# ---------------------------------------------------------------------------

def test_on_step_failed_callback_fires_with_reason():
    events = []
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s, on_step_failed=lambda sid, r: events.append((sid, r)))
    planner.mark_step_failed(s.step_id, "boom")
    assert events == [(s.step_id, "boom")]


def test_on_step_failed_callback_uses_default_reason():
    events = []
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s, on_step_failed=lambda sid, r: events.append((sid, r)))
    planner.mark_step_failed(s.step_id)
    assert events[0][1] == "step failed"


def test_on_step_failed_not_required():
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s)  # no callback
    planner.mark_step_failed(s.step_id)  # must not raise
    assert planner.get_plan().steps[0].status == "failed"


# ---------------------------------------------------------------------------
# mark_step_skipped with reason and callback
# ---------------------------------------------------------------------------

def test_on_step_skipped_callback_fires_with_reason():
    events = []
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s, on_step_skipped=lambda sid, r: events.append((sid, r)))
    planner.mark_step_skipped(s.step_id, "condition not met")
    assert events == [(s.step_id, "condition not met")]


def test_on_step_skipped_callback_uses_default_reason():
    events = []
    s = ContinuationStep(tool_name="t", description="d")
    planner = make_planner(s, on_step_skipped=lambda sid, r: events.append((sid, r)))
    planner.mark_step_skipped(s.step_id)
    assert events[0][1] == "condition not met"


# ---------------------------------------------------------------------------
# Propagation fires on_step_skipped for dependent steps
# ---------------------------------------------------------------------------

def test_propagation_fires_skipped_callback_for_dependants():
    skipped = []
    s1 = ContinuationStep(tool_name="t1", description="first")
    s2 = ContinuationStep(tool_name="t2", description="second", depends_on=[s1.step_id])
    s3 = ContinuationStep(tool_name="t3", description="third", depends_on=[s2.step_id])
    planner = make_planner(s1, s2, s3, on_step_skipped=lambda sid, r: skipped.append(sid))
    planner.mark_step_failed(s1.step_id)
    assert s2.step_id in skipped
    assert s3.step_id in skipped


def test_propagation_skipped_reason_mentions_failed_step():
    reasons = {}
    s1 = ContinuationStep(tool_name="t1", description="first")
    s2 = ContinuationStep(tool_name="t2", description="second", depends_on=[s1.step_id])
    planner = make_planner(s1, s2, on_step_skipped=lambda sid, r: reasons.update({sid: r}))
    planner.mark_step_failed(s1.step_id)
    assert s1.step_id in reasons[s2.step_id]
