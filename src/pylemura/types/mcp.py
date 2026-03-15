"""MCP configuration types — mirrors lemura/src/types/mcp.ts"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MCPTransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


@dataclass
class MCPServerConfig:
    name: str
    transport: MCPTransportType = MCPTransportType.STDIO
    # stdio transport
    command: Optional[str] = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    # http / sse transport
    url: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
