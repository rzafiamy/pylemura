"""Storage interfaces — mirrors lemura/src/types/storage.ts"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional


class IStorageAdapter(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]: ...

    @abstractmethod
    async def set(self, key: str, value: Any) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]: ...


class IScratchpadAdapter(ABC):
    @abstractmethod
    async def load(self, session_id: str) -> str: ...

    @abstractmethod
    async def save(self, session_id: str, content: str) -> None: ...
