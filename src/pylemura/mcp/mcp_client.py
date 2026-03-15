"""MCP client for a single server — mirrors lemura/src/mcp/MCPClient.ts
Supports stdio, http, and sse transports. Zero external dependencies.
"""
from __future__ import annotations
import asyncio
import json
import os
import urllib.request
import urllib.error
from typing import Any, Optional

from pylemura.types.errors import LemuraMCPConnectionError, LemuraMCPTimeoutError
from pylemura.types.mcp import MCPServerConfig, MCPTransportType


class MCPClient:
    """Connects to a single MCP server and performs JSON-RPC calls."""

    def __init__(self, config: MCPServerConfig) -> None:
        self._config = config
        self._process: Optional[asyncio.subprocess.Process] = None
        self._connected = False
        self._tools_cache: Optional[list[dict[str, Any]]] = None

    @property
    def name(self) -> str:
        return self._config.name

    async def connect(self) -> None:
        if self._connected:
            return
        if self._config.transport == MCPTransportType.STDIO:
            await self._connect_stdio()
        # HTTP and SSE are stateless; mark as connected immediately
        self._connected = True

    async def _connect_stdio(self) -> None:
        if not self._config.command:
            raise LemuraMCPConnectionError(self._config.name, "No command specified for stdio transport")

        env = {**os.environ, **self._config.env}
        try:
            self._process = await asyncio.create_subprocess_exec(
                self._config.command,
                *self._config.args,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            raise LemuraMCPConnectionError(self._config.name, str(e)) from e

    async def list_tools(self) -> list[dict[str, Any]]:
        if self._tools_cache is not None:
            return self._tools_cache
        result = await self._rpc_call("tools/list", {})
        tools = result.get("tools", [])
        self._tools_cache = tools
        return tools

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        result = await self._rpc_call("tools/call", {"name": tool_name, "arguments": args})
        # MCP returns content array; extract text
        content = result.get("content", [])
        parts = [c.get("text", "") for c in content if c.get("type") == "text"]
        return "\n".join(parts) if parts else json.dumps(result)

    async def _rpc_call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._connected:
            await self.connect()
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        if self._config.transport == MCPTransportType.STDIO:
            return await self._rpc_stdio(payload)
        elif self._config.transport in (MCPTransportType.HTTP, MCPTransportType.SSE):
            return await self._rpc_http(payload)
        else:
            raise LemuraMCPConnectionError(self._config.name, f"Unsupported transport: {self._config.transport}")

    async def _rpc_stdio(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._process is None:
            raise LemuraMCPConnectionError(self._config.name, "Process not started")
        line = json.dumps(payload) + "\n"
        loop = asyncio.get_event_loop()
        try:
            self._process.stdin.write(line.encode())
            await asyncio.wait_for(self._process.stdin.drain(), timeout=self._config.timeout)
            response_line = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=self._config.timeout
            )
        except asyncio.TimeoutError:
            raise LemuraMCPTimeoutError(self._config.name)
        except Exception as e:
            raise LemuraMCPConnectionError(self._config.name, str(e)) from e

        try:
            data = json.loads(response_line.decode().strip())
        except json.JSONDecodeError as e:
            raise LemuraMCPConnectionError(self._config.name, f"Invalid JSON response: {e}") from e

        if "error" in data:
            raise LemuraMCPConnectionError(self._config.name, str(data["error"]))
        return data.get("result", {})

    async def _rpc_http(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._config.url:
            raise LemuraMCPConnectionError(self._config.name, "No URL specified for HTTP transport")

        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._config.headers,
        }
        req = urllib.request.Request(self._config.url, data=body, headers=headers, method="POST")

        loop = asyncio.get_event_loop()
        try:
            def _do():
                with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                    return json.loads(resp.read().decode())
            data = await asyncio.wait_for(loop.run_in_executor(None, _do), timeout=self._config.timeout + 1)
        except asyncio.TimeoutError:
            raise LemuraMCPTimeoutError(self._config.name)
        except urllib.error.URLError as e:
            raise LemuraMCPConnectionError(self._config.name, str(e)) from e

        if "error" in data:
            raise LemuraMCPConnectionError(self._config.name, str(data["error"]))
        return data.get("result", {})

    async def disconnect(self) -> None:
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except Exception:
                self._process.kill()
        self._connected = False
        self._process = None
