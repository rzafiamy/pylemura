"""In-memory scratchpad adapter — mirrors lemura/src/context/InMemoryScratchpadAdapter.ts"""
from __future__ import annotations
from pylemura.types.storage import IScratchpadAdapter


class InMemoryScratchpadAdapter(IScratchpadAdapter):
    def __init__(self) -> None:
        self._pads: dict[str, str] = {}

    async def load(self, session_id: str) -> str:
        return self._pads.get(session_id, "")

    async def save(self, session_id: str, content: str) -> None:
        self._pads[session_id] = content
