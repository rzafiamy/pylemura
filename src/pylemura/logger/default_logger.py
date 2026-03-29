"""Colorized structured logger — mirrors lemura/src/logger/DefaultLogger.ts"""
from __future__ import annotations
import sys
import json
from datetime import datetime, timezone
from typing import Any, Optional

from pylemura.types.logger import ILogger, LogLevel


_RESET = "\033[0m"
_BOLD = "\033[1m"

_LEVEL_STYLES: dict[LogLevel, tuple[str, str]] = {
    LogLevel.DEBUG: ("\033[90m", "DBG"),
    LogLevel.INFO:  ("\033[36m", "INF"),
    LogLevel.WARN:  ("\033[33m", "WRN"),
    LogLevel.ERROR: ("\033[31m", "ERR"),
    LogLevel.FATAL: ("\033[35m", "FTL"),
}


class DefaultLogger(ILogger):
    def __init__(self, level: LogLevel = LogLevel.INFO, colorize: bool = True) -> None:
        self._level = level
        self._colorize = colorize and sys.stderr.isatty()

    def set_level(self, level: LogLevel) -> None:
        self._level = level

    def _emit(self, level: LogLevel, message: str, metadata: Optional[dict[str, Any]]) -> None:
        if level < self._level:
            return
        color, tag = _LEVEL_STYLES[level]
        ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
        problem_prefix = ">" if not self._colorize else "  \033[33m>"
        hint_prefix = "•" if not self._colorize else "  \033[90m•"
        if self._colorize:
            line = f"{color}{_BOLD}[{tag}]{_RESET} {color}{ts}{_RESET}  {message}"
        else:
            line = f"[{tag}] {ts}  {message}"

        if metadata:
            problem = metadata.pop("problem", None)
            hints = metadata.pop("hints", None)
            rest = {k: v for k, v in metadata.items() if v is not None}
            if rest:
                line += f"  {json.dumps(rest, default=str)}"
            if problem:
                line += f"\n  {problem_prefix}  Problem: {problem}"
            if hints:
                for h in hints:
                    line += f"\n  {hint_prefix}  {h}"
            if self._colorize:
                line += _RESET

        print(line, file=sys.stderr)

    def debug(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self._emit(LogLevel.DEBUG, message, dict(metadata) if metadata else None)

    def info(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self._emit(LogLevel.INFO, message, dict(metadata) if metadata else None)

    def warn(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self._emit(LogLevel.WARN, message, dict(metadata) if metadata else None)

    def error(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self._emit(LogLevel.ERROR, message, dict(metadata) if metadata else None)

    def fatal(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self._emit(LogLevel.FATAL, message, dict(metadata) if metadata else None)
