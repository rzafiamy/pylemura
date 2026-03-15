"""Tests for ShortTermMemoryRegistry."""
import pytest
from pylemura.context.short_term_memory_registry import ShortTermMemoryRegistry
from pylemura.context.in_memory_storage_adapter import InMemoryStorageAdapter


@pytest.fixture
def registry():
    return ShortTermMemoryRegistry(storage=InMemoryStorageAdapter())


@pytest.mark.asyncio
async def test_register_and_retrieve(registry: ShortTermMemoryRegistry):
    ref = await registry.register("Hello, world!", type="text")
    assert ref.startswith("[STM:")
    item = await registry.get_by_ref(ref)
    assert item is not None
    assert item.content == "Hello, world!"


@pytest.mark.asyncio
async def test_update(registry: ShortTermMemoryRegistry):
    ref = await registry.register("initial", type="text")
    item = await registry.get_by_ref(ref)
    await registry.update(item.id, {"content": "updated"})
    updated = await registry.get_by_ref(ref)
    assert updated.content == "updated"


@pytest.mark.asyncio
async def test_delete(registry: ShortTermMemoryRegistry):
    ref = await registry.register("to delete", type="text")
    item = await registry.get_by_ref(ref)
    await registry.delete(item.id)
    assert await registry.get_by_ref(ref) is None


@pytest.mark.asyncio
async def test_list_all(registry: ShortTermMemoryRegistry):
    await registry.register("first", type="text")
    await registry.register("second", type="text")
    items = await registry.list_all()
    assert len(items) == 2
