"""Tool registry & execution engine — mirrors lemura/src/tools/ToolRegistry.ts"""
from __future__ import annotations
import asyncio
import json
from typing import Any, Optional

from pylemura.tools.schema_validator import validate_json_schema, ValidationError as SchemaValidationError
from pylemura.types.errors import (
    LemuraToolNotFoundError,
    LemuraToolTimeoutError,
    LemuraToolValidationError,
)
from pylemura.types.logger import ILogger
from pylemura.types.tools import IToolDefinition, ToolContext

_DEFAULT_TIMEOUT = 30.0


class ToolRegistry:
    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._tools: dict[str, IToolDefinition] = {}
        self._timeout = timeout
        self._call_counts: dict[str, int] = {}

    # --- Registration ---

    def register(self, tool: IToolDefinition) -> None:
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[IToolDefinition]:
        return self._tools.get(name)

    def get_all(self) -> list[IToolDefinition]:
        return list(self._tools.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        """Return OpenAI-style tool schemas for all registered tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    # --- Execution ---

    async def execute(
        self,
        name: str,
        params: Any,
        context: ToolContext,
        timeout: Optional[float] = None,
    ) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise LemuraToolNotFoundError(name)

        # Validate params against JSON schema
        if isinstance(params, dict) and tool.parameters:
            try:
                validate_json_schema(params, tool.parameters)
            except SchemaValidationError as e:
                raise LemuraToolValidationError(name, str(e)) from e

        effective_timeout = timeout or self._timeout
        self._call_counts[name] = self._call_counts.get(name, 0) + 1

        try:
            return await asyncio.wait_for(
                tool.execute(params, context),
                timeout=effective_timeout,
            )
        except asyncio.TimeoutError:
            raise LemuraToolTimeoutError(name, effective_timeout)

    async def execute_parallel(
        self,
        calls: list[dict[str, Any]],
        context: ToolContext,
        timeout: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Execute multiple tool calls concurrently. Returns results with id, result|error."""

        async def _run_one(call: dict[str, Any]) -> dict[str, Any]:
            call_id = call["id"]
            name = call["name"]
            params = call.get("params", {})
            try:
                result = await self.execute(name, params, context, timeout)
                return {"id": call_id, "result": result}
            except Exception as exc:
                return {"id": call_id, "error": exc}

        return await asyncio.gather(*[_run_one(c) for c in calls])

    def get_call_count(self, name: str) -> int:
        return self._call_counts.get(name, 0)

    def reset_call_counts(self) -> None:
        self._call_counts.clear()
