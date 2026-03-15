"""Tests for SessionManager using a mock adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from pylemura.agent.session_manager import SessionManager
from pylemura.types.adapters import (
    CompletionResponse,
    IProviderAdapter,
    ModelInfo,
    TokenUsage,
)
from pylemura.types.agent import SessionConfig
from pylemura.types.tools import FunctionTool, ToolContext


def make_mock_adapter(response_text: str = "Hello!", tool_calls=None) -> IProviderAdapter:
    adapter = MagicMock(spec=IProviderAdapter)
    adapter.name = "mock"
    adapter.version = "0.0.1"
    adapter.estimate_tokens = lambda t: max(1, len(t) // 4)
    adapter.get_model_info.return_value = ModelInfo(id="mock", context_window=4096)
    resp = CompletionResponse(
        content=response_text,
        tool_calls=tool_calls or [],
        finish_reason="stop",
        usage=TokenUsage(10, 20, 30),
    )
    adapter.complete = AsyncMock(return_value=resp)
    return adapter


@pytest.mark.asyncio
async def test_simple_run():
    adapter = make_mock_adapter("Hello from mock!")
    config = SessionConfig(adapter=adapter, model="mock-model", max_tokens=4096)
    session = SessionManager(config)
    result = await session.run("Hi there")
    assert result == "Hello from mock!"


@pytest.mark.asyncio
async def test_run_with_tool():
    from pylemura.types.adapters import ToolCall

    tool_call = ToolCall(id="call_1", name="greet", arguments='{"name": "World"}')

    call_count = 0

    def make_adapter_seq():
        adapter = MagicMock(spec=IProviderAdapter)
        adapter.name = "mock"
        adapter.version = "0.0.1"
        adapter.estimate_tokens = lambda t: max(1, len(t) // 4)
        adapter.get_model_info.return_value = ModelInfo(id="mock", context_window=4096)

        nonlocal call_count
        responses = [
            CompletionResponse(content="", tool_calls=[tool_call], finish_reason="tool_calls"),
            CompletionResponse(content="Done!", tool_calls=[], finish_reason="stop"),
        ]

        async def _complete(req):
            nonlocal call_count
            r = responses[min(call_count, len(responses) - 1)]
            call_count += 1
            return r

        adapter.complete = _complete
        return adapter

    adapter = make_adapter_seq()

    async def _greet(params, ctx: ToolContext):
        return f"Hello, {params['name']}!"

    greet_tool = FunctionTool(
        name="greet",
        description="Greet someone",
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        func=_greet,
    )

    config = SessionConfig(
        adapter=adapter,
        model="mock-model",
        max_tokens=4096,
        tools=[greet_tool],
    )
    session = SessionManager(config)
    result = await session.run("Please greet the world")
    assert result == "Done!"
    assert call_count == 2


@pytest.mark.asyncio
async def test_history_persistence():
    adapter = make_mock_adapter("Response 1")
    config = SessionConfig(adapter=adapter, model="mock-model", max_tokens=4096)
    session = SessionManager(config)
    await session.run("First message")
    history = session.get_history()
    # Should have user turn + assistant turn
    assert any(t.role == "user" for t in history)
    assert any(t.role == "assistant" for t in history)


@pytest.mark.asyncio
async def test_reset_clears_history():
    adapter = make_mock_adapter("Hi!")
    config = SessionConfig(adapter=adapter, model="mock-model", max_tokens=4096)
    session = SessionManager(config)
    await session.run("Hello")
    await session.reset()
    assert session.get_history() == []
