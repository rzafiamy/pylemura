"""MCP client registry — mirrors lemura/src/mcp/MCPClientRegistry.ts"""
from __future__ import annotations
from typing import Any, Optional

from pylemura.mcp.mcp_client import MCPClient
from pylemura.types.logger import ILogger
from pylemura.types.mcp import MCPServerConfig
from pylemura.types.tools import FunctionTool, IToolDefinition


class MCPClientRegistry:
    def __init__(self, logger: ILogger) -> None:
        self._logger = logger
        self._clients: dict[str, MCPClient] = {}
        self._tool_map: dict[str, tuple[MCPClient, str]] = {}  # tool_name -> (client, original_name)

    async def register(self, name: str, config: MCPServerConfig) -> None:
        client = MCPClient(config)
        self._clients[name] = client
        self._logger.debug(f"[MCP] Registered server '{name}'")

    async def connect_all(self) -> None:
        for name, client in self._clients.items():
            try:
                await client.connect()
                self._logger.info(f"[MCP] Connected to '{name}'")
            except Exception as e:
                self._logger.error(f"[MCP] Failed to connect to '{name}': {e}")

    async def discover_tools(self) -> list[IToolDefinition]:
        tools: list[IToolDefinition] = []
        for server_name, client in self._clients.items():
            try:
                raw_tools = await client.list_tools()
                for t in raw_tools:
                    tool_name = f"mcp__{server_name}__{t.get('name', 'unknown')}"
                    original_name = t.get("name", "unknown")
                    self._tool_map[tool_name] = (client, original_name)
                    tools.append(self._wrap_tool(tool_name, t, client, original_name))
            except Exception as e:
                self._logger.warn(f"[MCP] Failed to discover tools from '{server_name}': {e}")
        return tools

    def _wrap_tool(
        self,
        tool_name: str,
        schema: dict[str, Any],
        client: MCPClient,
        original_name: str,
    ) -> FunctionTool:
        description = schema.get("description", f"MCP tool: {original_name}")
        parameters = schema.get("inputSchema") or schema.get("parameters") or {"type": "object", "properties": {}}

        async def _exec(params: Any, ctx: Any) -> Any:
            return await client.call_tool(original_name, params or {})

        return FunctionTool(
            name=tool_name,
            description=description,
            parameters=parameters,
            func=_exec,
        )

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        if tool_name not in self._tool_map:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
        client, original_name = self._tool_map[tool_name]
        return await client.call_tool(original_name, args)

    async def disconnect_all(self) -> None:
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()
        self._tool_map.clear()

    def get_registered_servers(self) -> list[str]:
        return list(self._clients.keys())
