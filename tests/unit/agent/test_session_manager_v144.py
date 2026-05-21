"""Tests for SessionManager v1.4.4 additions."""
import dataclasses
import pytest
from unittest.mock import AsyncMock, MagicMock

from pylemura.agent.session_manager import SessionManager
from pylemura.agent.execution.continuation_planner import (
    ContinuationStep,
    StepVerifier,
    StepVerifierResult,
)
from pylemura.types.adapters import (
    CompletionResponse,
    IProviderAdapter,
    ModelInfo,
    ToolCall,
    TokenUsage,
)
from pylemura.types.agent import SessionConfig
from pylemura.types.tools import FunctionTool, ToolContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_adapter(*responses: CompletionResponse) -> IProviderAdapter:
    """Adapter that returns responses in sequence."""
    adapter = MagicMock(spec=IProviderAdapter)
    adapter.name = "mock"
    adapter.version = "0.0.1"
    adapter.estimate_tokens = lambda t: max(1, len(t) // 4)
    adapter.get_model_info.return_value = ModelInfo(id="mock", context_window=4096)
    adapter.complete = AsyncMock(side_effect=list(responses))
    return adapter


def make_fetch_tool(result: str = "some data") -> FunctionTool:
    async def _fetch(params, ctx: ToolContext):
        return result
    return FunctionTool(
        name="fetch",
        description="fetch data",
        parameters={"type": "object", "properties": {}},
        func=_fetch,
    )


def scripted_session(*responses, tools=None) -> SessionManager:
    adapter = make_adapter(*responses)
    config = SessionConfig(
        adapter=adapter,
        model="mock-model",
        max_tokens=4096,
        tools=tools or [],
    )
    return SessionManager(config)


# ---------------------------------------------------------------------------
# get_plan()
# ---------------------------------------------------------------------------

def test_get_plan_returns_none_when_not_set():
    adapter = make_adapter(
        CompletionResponse(content="hi", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2))
    )
    session = SessionManager(SessionConfig(adapter=adapter, model="m", max_tokens=4096))
    assert session.get_plan() is None


@pytest.mark.asyncio
async def test_get_plan_returns_plan_after_set_plan():
    step = ContinuationStep(tool_name="fetch", description="fetch data")
    adapter = make_adapter(
        CompletionResponse(content="done", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2))
    )
    session = SessionManager(SessionConfig(adapter=adapter, model="m", max_tokens=4096))
    session.set_plan([step])
    plan = session.get_plan()
    assert plan is not None
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "fetch"


@pytest.mark.asyncio
async def test_get_plan_after_run_reflects_step_statuses():
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")
    step = ContinuationStep(tool_name="fetch", description="fetch data")

    session = scripted_session(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
        tools=[make_fetch_tool()],
    )
    session.set_plan([step])
    await session.run("go")

    plan = session.get_plan()
    assert plan is not None
    assert plan.steps[0].status == "done"


# ---------------------------------------------------------------------------
# max_completion_tokens default changed to 4000
# ---------------------------------------------------------------------------

def test_max_completion_tokens_default_is_4000():
    field_map = {f.name: f.default for f in dataclasses.fields(SessionConfig)}
    assert field_map["max_completion_tokens"] == 4000


# ---------------------------------------------------------------------------
# Config warnings: max_steps vs max_iterations
# ---------------------------------------------------------------------------

def test_warns_when_max_steps_exceeds_default_max_iterations(capsys):
    adapter = make_adapter(
        CompletionResponse(content="hi", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2))
    )
    SessionManager(SessionConfig(
        adapter=adapter, model="m", max_tokens=4096,
        max_steps=50,         # > default 10
        max_iterations=None,  # not set
    ))
    stderr = capsys.readouterr().err
    assert "max_steps" in stderr and "max_iterations" in stderr


def test_warns_when_max_steps_much_larger_than_max_iterations(capsys):
    adapter = make_adapter(
        CompletionResponse(content="hi", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2))
    )
    SessionManager(SessionConfig(
        adapter=adapter, model="m", max_tokens=4096,
        max_steps=500,
        max_iterations=3,
    ))
    stderr = capsys.readouterr().err
    assert "max_steps" in stderr and "max_iterations" in stderr


def test_no_warning_when_max_steps_fits_max_iterations(capsys):
    adapter = make_adapter(
        CompletionResponse(content="hi", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2))
    )
    SessionManager(SessionConfig(
        adapter=adapter, model="m", max_tokens=4096,
        max_steps=10,
        max_iterations=5,
    ))
    stderr = capsys.readouterr().err
    # Should not warn about max_steps/max_iterations mismatch
    assert not ("max_steps" in stderr and "max_iterations" in stderr)


# ---------------------------------------------------------------------------
# StepVerifier — pass verdict
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verifier_pass_step_marked_done():
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")
    step = ContinuationStep(
        tool_name="fetch",
        description="fetch data",
        verify=StepVerifier(check=lambda out, args: StepVerifierResult(status="pass")),
    )
    session = scripted_session(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
        tools=[make_fetch_tool()],
    )
    session.set_plan([step])
    result = await session.run("go")
    assert result == "Done!"
    assert session.get_plan().steps[0].status == "done"


# ---------------------------------------------------------------------------
# StepVerifier — fail verdict
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verifier_fail_marks_step_failed():
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")
    step = ContinuationStep(
        tool_name="fetch",
        description="fetch data",
        verify=StepVerifier(check=lambda out, args: StepVerifierResult(status="fail", reason="bad")),
    )
    session = scripted_session(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
        tools=[make_fetch_tool()],
    )
    session.set_plan([step])
    await session.run("go")
    assert session.get_plan().steps[0].status == "failed"


@pytest.mark.asyncio
async def test_verifier_fail_propagates_skip_to_dependants():
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")
    s1 = ContinuationStep(
        tool_name="fetch",
        description="fetch",
        verify=StepVerifier(check=lambda o, a: StepVerifierResult(status="fail")),
    )
    s2 = ContinuationStep(tool_name="process", description="process", depends_on=[s1.step_id])

    session = scripted_session(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
        tools=[make_fetch_tool()],
    )
    session.set_plan([s1, s2])
    await session.run("go")
    plan = session.get_plan()
    assert plan.steps[0].status == "failed"
    assert plan.steps[1].status == "skipped"


# ---------------------------------------------------------------------------
# StepVerifier — retry verdict
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verifier_retry_with_no_retries_left_marks_failed():
    """max_retries=0 means a 'retry' verdict immediately becomes 'failed'."""
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")
    step = ContinuationStep(
        tool_name="fetch",
        description="fetch data",
        verify=StepVerifier(
            check=lambda out, args: StepVerifierResult(status="retry", reason="empty"),
            max_retries=0,
        ),
    )
    session = scripted_session(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
        tools=[make_fetch_tool()],
    )
    session.set_plan([step])
    await session.run("go")
    assert session.get_plan().steps[0].status == "failed"


# ---------------------------------------------------------------------------
# StepVerifier — async check function
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verifier_async_check_function():
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")

    async def async_check(out, args):
        return StepVerifierResult(status="pass")

    step = ContinuationStep(
        tool_name="fetch",
        description="fetch data",
        verify=StepVerifier(check=async_check),
    )
    session = scripted_session(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
        tools=[make_fetch_tool()],
    )
    session.set_plan([step])
    result = await session.run("go")
    assert result == "Done!"
    assert session.get_plan().steps[0].status == "done"


# ---------------------------------------------------------------------------
# Verification trace events emitted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verifier_fail_emits_verification_trace():
    tool_call = ToolCall(id="c1", name="fetch", arguments="{}")
    step = ContinuationStep(
        tool_name="fetch",
        description="fetch data",
        verify=StepVerifier(check=lambda o, a: StepVerifierResult(status="fail", reason="bad")),
    )
    trace_events = []
    adapter = make_adapter(
        CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls", usage=TokenUsage(1, 1, 2)),
        CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop", usage=TokenUsage(1, 1, 2)),
    )
    config = SessionConfig(
        adapter=adapter, model="m", max_tokens=4096,
        tools=[make_fetch_tool()],
        on_trace=lambda e: trace_events.append(e),
    )
    session = SessionManager(config)
    session.set_plan([step])
    await session.run("go")
    verification_events = [e for e in trace_events if e.type == "verification"]
    assert len(verification_events) >= 1
    assert verification_events[0].name == "step_failed"
