"""Built-in STM tools — mirrors lemura/src/tools/builtin/short_term_memory.ts"""
from __future__ import annotations
from typing import Any

from pylemura.types.tools import FunctionTool, ToolContext


async def _read_chunk(params: Any, ctx: ToolContext) -> str:
    if ctx.stm_registry is None:
        return "Error: STM registry not available"
    ref = params.get("ref", "")
    start = params.get("start", 0)
    end = params.get("end")
    item = await ctx.stm_registry.get_by_ref(ref)
    if item is None:
        return f"Error: STM item '{ref}' not found"
    content = str(item.content)
    return content[start:end] if end is not None else content[start:]


async def _search_chunk(params: Any, ctx: ToolContext) -> str:
    if ctx.stm_registry is None:
        return "Error: STM registry not available"
    ref = params.get("ref", "")
    query = params.get("query", "").lower()
    item = await ctx.stm_registry.get_by_ref(ref)
    if item is None:
        return f"Error: STM item '{ref}' not found"
    lines = str(item.content).splitlines()
    matches = [f"L{i+1}: {line}" for i, line in enumerate(lines) if query in line.lower()]
    return "\n".join(matches) if matches else "No matches found"


async def _list_chunks(params: Any, ctx: ToolContext) -> str:
    if ctx.stm_registry is None:
        return "Error: STM registry not available"
    items = await ctx.stm_registry.list_all()
    if not items:
        return "No STM items registered"
    lines = [f"- {item.ref} [{item.type}] {item.token_count} tokens" for item in items]
    return "\n".join(lines)


async def _update_chunk(params: Any, ctx: ToolContext) -> str:
    if ctx.stm_registry is None:
        return "Error: STM registry not available"
    ref = params.get("ref", "")
    item = await ctx.stm_registry.get_by_ref(ref)
    if item is None:
        return f"Error: STM item '{ref}' not found"
    mode = params.get("mode", "append")
    new_content = params.get("content", "")
    if mode == "append":
        updated = str(item.content) + "\n" + new_content
    else:
        updated = new_content
    await ctx.stm_registry.update(item.id, {"content": updated})
    return f"Updated {ref} ({mode})"


async def _read_scratchpad(params: Any, ctx: ToolContext) -> str:
    return ctx.scratchpad or "(empty)"


async def _write_scratchpad(params: Any, ctx: ToolContext) -> str:
    if ctx.scratchpad_adapter is None:
        return "Error: scratchpad adapter not available"
    content = params.get("content", "")
    await ctx.scratchpad_adapter.save(ctx.session_id, content)
    return "Scratchpad updated"


def make_stm_tools() -> list[FunctionTool]:
    return [
        FunctionTool(
            name="read_chunk",
            description="Read a portion of a short-term memory item by its STM reference.",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "STM reference like [STM:uuid]"},
                    "start": {"type": "integer", "description": "Start character offset"},
                    "end": {"type": "integer", "description": "End character offset (optional)"},
                },
                "required": ["ref"],
            },
            func=_read_chunk,
        ),
        FunctionTool(
            name="search_chunk",
            description="Search for a keyword within a short-term memory item.",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string"},
                    "query": {"type": "string", "description": "Keyword to search"},
                },
                "required": ["ref", "query"],
            },
            func=_search_chunk,
        ),
        FunctionTool(
            name="list_chunks",
            description="List all registered short-term memory items.",
            parameters={"type": "object", "properties": {}},
            func=_list_chunks,
        ),
        FunctionTool(
            name="update_chunk",
            description="Append to or replace a short-term memory item.",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string"},
                    "content": {"type": "string"},
                    "mode": {"type": "string", "enum": ["append", "replace"]},
                },
                "required": ["ref", "content"],
            },
            func=_update_chunk,
        ),
        FunctionTool(
            name="read_scratchpad",
            description="Read the agent's current scratchpad content.",
            parameters={"type": "object", "properties": {}},
            func=_read_scratchpad,
        ),
        FunctionTool(
            name="write_scratchpad",
            description="Write content to the agent's scratchpad.",
            parameters={
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
            func=_write_scratchpad,
        ),
    ]
