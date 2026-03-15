"""Short-term memory registry — mirrors lemura/src/context/ShortTermMemoryRegistry.ts"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

from pylemura.types.storage import IStorageAdapter

STMType = Literal["text", "blob"]
_STM_PREFIX = "stm:"


@dataclass
class STMItem:
    id: str
    ref: str           # '[STM:uuid]'
    content: Any
    type: STMType
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int = 0


class ShortTermMemoryRegistry:
    def __init__(
        self,
        storage: IStorageAdapter,
        estimate_tokens: Optional[Callable[[str], int]] = None,
    ) -> None:
        self._storage = storage
        self._estimate_tokens = estimate_tokens or (lambda t: max(1, len(str(t)) // 4))

    async def register(
        self,
        content: Any,
        type: STMType = "text",
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        item_id = str(uuid.uuid4())
        ref = f"[STM:{item_id}]"
        token_count = self._estimate_tokens(str(content)) if type == "text" else 0
        item = STMItem(
            id=item_id,
            ref=ref,
            content=content,
            type=type,
            metadata=metadata or {},
            token_count=token_count,
        )
        await self._storage.set(f"{_STM_PREFIX}{item_id}", item)
        return ref

    async def get_by_ref(self, ref: str) -> Optional[STMItem]:
        # Extract id from '[STM:uuid]'
        if ref.startswith("[STM:") and ref.endswith("]"):
            item_id = ref[5:-1]
            return await self._storage.get(f"{_STM_PREFIX}{item_id}")
        return None

    async def get_by_id(self, item_id: str) -> Optional[STMItem]:
        return await self._storage.get(f"{_STM_PREFIX}{item_id}")

    async def update(
        self,
        item_id: str,
        updates: dict[str, Any],
    ) -> None:
        item: Optional[STMItem] = await self._storage.get(f"{_STM_PREFIX}{item_id}")
        if item is None:
            return
        if "content" in updates:
            item.content = updates["content"]
            if item.type == "text":
                item.token_count = self._estimate_tokens(str(item.content))
        if "metadata" in updates:
            item.metadata.update(updates["metadata"])
        await self._storage.set(f"{_STM_PREFIX}{item_id}", item)

    async def delete(self, item_id: str) -> None:
        await self._storage.delete(f"{_STM_PREFIX}{item_id}")

    async def list_all(self) -> list[STMItem]:
        keys = await self._storage.list_keys(_STM_PREFIX)
        items = []
        for key in keys:
            item = await self._storage.get(key)
            if item is not None:
                items.append(item)
        return items
