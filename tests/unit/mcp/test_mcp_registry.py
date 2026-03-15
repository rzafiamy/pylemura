"""Tests for MCPClientRegistry (unit — no real servers)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pylemura.mcp.mcp_client_registry import MCPClientRegistry
from pylemura.logger.default_logger import DefaultLogger
from pylemura.types.mcp import MCPServerConfig, MCPTransportType


def make_registry():
    return MCPClientRegistry(logger=DefaultLogger())


@pytest.mark.asyncio
async def test_register_server():
    registry = make_registry()
    config = MCPServerConfig(name="test", transport=MCPTransportType.HTTP, url="http://localhost:8080")
    await registry.register("test", config)
    assert "test" in registry.get_registered_servers()


@pytest.mark.asyncio
async def test_discover_tools_with_mock_client():
    registry = make_registry()
    config = MCPServerConfig(name="test", transport=MCPTransportType.HTTP, url="http://localhost:8080")
    await registry.register("test", config)

    mock_client = AsyncMock()
    mock_client.list_tools.return_value = [
        {"name": "search", "description": "Search tool", "inputSchema": {"type": "object", "properties": {}}}
    ]
    registry._clients["test"] = mock_client

    tools = await registry.discover_tools()
    assert len(tools) == 1
    assert tools[0].name == "mcp__test__search"
