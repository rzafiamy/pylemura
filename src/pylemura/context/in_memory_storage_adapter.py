"""In-memory storage adapter — mirrors lemura/src/context/InMemoryStorageAdapter.ts"""
from __future__ import annotations
from typing import Any, Optional
from pylemura.types.storage import IStorageAdapter


class InMemoryStorageAdapter(IStorageAdapter):
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    async def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def list_keys(self, prefix: str = "") -> list[str]:
        return [k for k in self._store if k.startswith(prefix)]
