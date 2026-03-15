"""Lemura error hierarchy — mirrors lemura/src/types/errors.ts"""
from __future__ import annotations
from typing import Optional


class LemuraError(Exception):
    """Base error for all pylemura errors."""

    def __init__(
        self,
        message: str,
        code: str = "LEMURA_ERROR",
        problem: Optional[str] = None,
        hints: Optional[list[str]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.problem = problem
        self.hints: list[str] = hints or []

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.problem:
            parts.append(f"Problem: {self.problem}")
        if self.hints:
            parts.append("Hints: " + "; ".join(self.hints))
        return " | ".join(parts)


class LemuraContextOverflowError(LemuraError):
    def __init__(self, message: str = "Context window exceeded", **kwargs) -> None:
        super().__init__(message, code="CONTEXT_OVERFLOW", **kwargs)


class LemuraToolNotFoundError(LemuraError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' not found",
            code="TOOL_NOT_FOUND",
            problem=f"No tool named '{tool_name}' is registered",
            hints=[
                "Check the tool name spelling",
                "Ensure the tool was registered before calling",
            ],
        )


class LemuraAdapterError(LemuraError):
    def __init__(
        self,
        message: str,
        problem: Optional[str] = None,
        hints: Optional[list[str]] = None,
    ) -> None:
        super().__init__(
            message, code="ADAPTER_ERROR", problem=problem, hints=hints
        )


class LemuraSkillInjectionError(LemuraError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="SKILL_INJECTION_ERROR")


class LemuraMaxIterationsError(LemuraError):
    def __init__(self, max_iterations: int) -> None:
        super().__init__(
            f"Max iterations ({max_iterations}) reached",
            code="MAX_ITERATIONS",
            problem="The agent exceeded its allowed number of ReAct iterations",
            hints=[
                "Increase max_iterations in SessionConfig",
                "Simplify the task or break it into smaller steps",
            ],
        )


class LemuraToolValidationError(LemuraError):
    def __init__(self, tool_name: str, details: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' parameter validation failed: {details}",
            code="TOOL_VALIDATION_ERROR",
            problem=details,
        )


class LemuraToolTimeoutError(LemuraError):
    def __init__(self, tool_name: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Tool '{tool_name}' timed out after {timeout_seconds}s",
            code="TOOL_TIMEOUT",
            problem=f"Tool execution exceeded {timeout_seconds}s",
            hints=["Increase the tool timeout", "Optimize the tool implementation"],
        )


class LemuraMCPError(LemuraError):
    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message, code="MCP_ERROR", **kwargs)


class LemuraMCPConnectionError(LemuraMCPError):
    def __init__(self, server_name: str, reason: str) -> None:
        super().__init__(
            f"Failed to connect to MCP server '{server_name}': {reason}",
        )
        self.code = "MCP_CONNECTION_ERROR"


class LemuraMCPTimeoutError(LemuraMCPError):
    def __init__(self, server_name: str) -> None:
        super().__init__(f"MCP server '{server_name}' connection timed out")
        self.code = "MCP_TIMEOUT"
