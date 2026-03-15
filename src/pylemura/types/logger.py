"""Logger interface — mirrors lemura/src/types/logger.ts"""
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Optional


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    FATAL = 4


class LogMetadata(dict):
    """Arbitrary structured metadata attached to log entries."""


class ILogger(ABC):
    @abstractmethod
    def debug(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None: ...

    @abstractmethod
    def info(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None: ...

    @abstractmethod
    def warn(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None: ...

    @abstractmethod
    def error(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None: ...

    @abstractmethod
    def fatal(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None: ...

    @abstractmethod
    def set_level(self, level: LogLevel) -> None: ...
