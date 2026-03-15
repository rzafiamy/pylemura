"""Tool response processor — mirrors lemura/src/agent/execution/ToolResponseProcessor.ts"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from pylemura.types.tools import IToolResponseProcessor, ToolContext

_SMALL = 200
_MEDIUM = 800
_LARGE = 2000


@dataclass
class ToolResponseProcessorConfig:
    relevance_threshold: float = 0.0
    max_response_tokens: int = 2000
    error_patterns: list[str] = None  # type: ignore

    def __post_init__(self):
        if self.error_patterns is None:
            self.error_patterns = ["error:", "exception:", "traceback", "failed to", "could not"]


class ToolResponseProcessor(IToolResponseProcessor):
    def __init__(self, config: Optional[ToolResponseProcessorConfig] = None) -> None:
        self._cfg = config or ToolResponseProcessorConfig()

    def evaluate(self, response: str, tool_name: str, context: ToolContext) -> dict[str, Any]:
        token_count = max(1, len(response) // 4)

        if token_count <= _SMALL:
            size_class = "small"
        elif token_count <= _MEDIUM:
            size_class = "medium"
        elif token_count <= _LARGE:
            size_class = "large"
        else:
            size_class = "oversized"

        lower = response.lower()
        error_detected = any(pat in lower for pat in self._cfg.error_patterns)

        should_compress = (
            size_class in ("large", "oversized")
            and token_count > self._cfg.max_response_tokens
        )

        # Simple heuristic: non-empty, non-error response is considered answered
        answered = bool(response.strip()) and not error_detected

        return {
            "token_count": token_count,
            "size_class": size_class,
            "should_compress": should_compress,
            "answered": answered,
            "error_detected": error_detected,
            "suggested_action": "compress" if should_compress else ("retry" if error_detected else "accept"),
        }

    def compress(self, response: str, evaluation: dict[str, Any]) -> str:
        size_class = evaluation.get("size_class", "small")
        max_tokens = self._cfg.max_response_tokens
        max_chars = max_tokens * 4

        if size_class == "oversized":
            # Head + tail truncation
            half = max_chars // 2
            if len(response) <= max_chars:
                return response
            return response[:half] + f"\n... [{len(response) - max_chars} chars omitted] ...\n" + response[-half:]

        if size_class == "large":
            # Keep first + last N lines
            lines = response.splitlines()
            keep = max(5, max_tokens // 20)
            if len(lines) <= keep * 2:
                return response
            kept_lines = lines[:keep] + [f"... [{len(lines) - keep * 2} lines omitted] ..."] + lines[-keep:]
            return "\n".join(kept_lines)

        return response
