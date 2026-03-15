# pylemura

**Provider-agnostic agentic AI runtime for Python** — Python portage of [lemura](https://github.com/yourusername/lemura).

pylemura implements a complete **ReAct (Reasoning + Acting)** loop orchestration system with enterprise-grade features: context compression, skill injection, tool management, short-term memory, RAG, MCP support, and multimodal capabilities.

**Zero required dependencies** — only Python stdlib.

## Quick Start

```python
import asyncio
from pylemura import SessionManager, OpenAICompatibleAdapter, DefaultLogger, LogLevel

async def main():
    adapter = OpenAICompatibleAdapter()  # reads OPENAI_API_KEY from env

    session = SessionManager(
        adapter=adapter,
        model="gpt-4o-mini",
        max_tokens=100_000,
    )

    response = await session.run("What is the capital of France?")
    print(response)

asyncio.run(main())
```

## Features

- **ReAct loop** — iterative reasoning + tool execution
- **Context compression** — sandwich, history, and summary injection strategies
- **Skill injection** — fixed and dynamic skills with tiered content
- **Tool registry** — JSON Schema validation, timeouts, parallel execution
- **Short-term memory (STM)** — chunked in-session storage
- **RAG adapter** — pluggable retrieval-augmented generation
- **MCP support** — Model Context Protocol client (stdio, http, sse)
- **Media bridge** — transcription, synthesis, vision, image generation
- **Goal planning** — automatic sub-goal decomposition
- **Continuation planning** — multi-step tool orchestration
- **Tool firewall** — accept/deny/ask rules
- **Streaming** — full async generator streaming
- **Zero dependencies** — core runs on Python stdlib only

## Installation

```bash
pip install pylemura
```

## Architecture

```
pylemura/
├── agent/          # SessionManager + ReAct execution engine
├── adapters/       # OpenAI-compatible provider adapter
├── context/        # Context compression strategies + STM
├── tools/          # Tool registry, firewall, schema validation
├── skills/         # Skill injection system
├── mcp/            # Model Context Protocol client
├── media/          # MediaBridge (ASR, TTS, vision)
├── rag/            # RAG adapter interface + in-memory impl
├── logger/         # Colorized structured logging
└── types/          # All type definitions
```

## License

MIT
