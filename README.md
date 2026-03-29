# pylemura

**A provider-agnostic, premium agentic AI runtime for Python.**

[![PyPI version](https://img.shields.io/pypi/v/pylemura.svg?style=flat-square)](https://pypi.org/project/pylemura/)
[![license](https://img.shields.io/pypi/l/pylemura.svg?style=flat-square)](./LICENSE)
[![docs](https://img.shields.io/badge/docs-lemura.makix.fr-blue?style=flat-square)](https://lemura.makix.fr)
[![build](https://img.shields.io/github/actions/workflow/status/rzafiamy/pylemura/ci.yml?branch=main&style=flat-square)](https://github.com/rzafiamy/pylemura/actions)

---

**🚀 v1.1.0 is available. Read the [Release Notes](./RELEASE_NOTES.md).**

---

`pylemura` is a robust, provider-agnostic Python package designed to encapsulate a full agentic AI runtime. It simplifies the complex orchestration of LLMs, tools, and context management into a single, cohesive interface. It is the official Python portage of [lemura](https://github.com/rzafiamy/lemura).

### ✨ Key Features
- **🧠 Dynamic Skill Market**: Switch skills on/off at runtime via tags, names, or tool dependencies.
- **🗺️ Continuation Planning**: Multi-step tool chains with parallel execution and conditional logic.
- **🎯 Intelligent Goal Maintenance**: LLM-powered sub-goal decomposition and status tracking.
- **🔌 MCP Support**: Native Model Context Protocol integration for connecting to external tool servers.
- **🛡️ Tool Firewall**: Fully integrated ask/accept/deny policy layer for security.
- **⚡ Parallel Tool Calls**: Execute independent tools concurrently for reduced latency.
- **🧹 Summary Injection**: Ensures the model never "forgets" what was compressed away.
- **📊 Enhanced Observability**: Detailed tracing, token tracking, and execution budget enforcement.
- **🌊 Native Streaming**: Full async generator support for token-by-token completion.
- **📦 Zero Dependencies**: Core runtime runs on the Python standard library only.

## 🚀 Install

```bash
pip install pylemura
```

## ⚙️ Environment Variables

The built-in `OpenAICompatibleAdapter` can be configured using environment variables. To load them from a `.env` file, you can use `python-dotenv`:

```bash
pip install python-dotenv
```

Then at the very top of your entry point:

```python
from dotenv import load_dotenv
load_dotenv()
```

Create a `.env` file in your project root:

```ini
# Provider Configuration (OpenAI, Groq, Together, Ollama, etc.)
LEMURA_API_KEY=your_api_key_here
LEMURA_BASE_URL=https://api.openai.com/v1
LEMURA_MODEL=gpt-4o-mini

# Fallbacks (Lemura also checks standard OpenAI variables)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## ⚡ Quick Start

```python
import asyncio
from pylemura import SessionManager, OpenAICompatibleAdapter

async def main():
    adapter = OpenAICompatibleAdapter(
        base_url="https://api.openai.com/v1",
        api_key="your_api_key_here",
        default_model="gpt-4o-mini"
    )

    session = SessionManager(
        adapter=adapter,
        model="gpt-4o-mini",
        max_tokens=100000,
    )

    response = await session.run("What is lemura?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧠 Core Concepts

Explore the architecture and advanced capabilities of `lemura` at [lemura.makix.fr](https://lemura.makix.fr):

- 🏁 **Getting Started** — Fundamental setup and concepts.
- 🧹 **Context Management** — Advanced compression strategies.
- 🔌 **Adapters** — Connecting to OpenAI, Groq, Anthropic, and more.
- 🛠️ **Tools and Skills** — Extending agent capabilities.
- 🎛️ **Media Bridge** — ASR, TTS, vision, and image generation.
- ⚡ **Advanced Execution** — Goal planning and continuation.

## 📦 API Overview

| Component | Description |
|---|---|
| `SessionManager` | The main entry point orchestrating the ReAct loop and tools. |
| `ContextManager` | Manages the conversation history using compression strategies. |
| `OpenAICompatibleAdapter` | Reference adapter for OpenAI, Groq, Together, etc. |
| `ToolRegistry` | Registers and executes tools for the agent. |
| `SkillInjector` | Loads and formats YAML/Markdown skills into system prompts. |
| `DefaultLogger` | Colorized logger with Problem/Hints metadata support. |

## 🪵 Logging and Tracing

`pylemura` features a premium, structured logging system designed for developer experience. It provides colorized output and actionable hints for errors.

```python
from pylemura import SessionManager, DefaultLogger, LogLevel

logger = DefaultLogger()
logger.set_level(LogLevel.DEBUG) # Set to show trace-level information

session = SessionManager(
    adapter=adapter,
    model="gpt-4o-mini",
    max_tokens=100000,
    logger=logger # Inject the logger
)
```

## 🔌 Provider Adapters

`pylemura` interacts with LLMs exclusively through the `IProviderAdapter` interface, ensuring zero lock-in.

| Adapter | Status | Description |
|---|---|---|
| `OpenAICompatibleAdapter` | ✅ Built-in | Wrapper for OpenAI and API-compatible endpoints. |

## 🤝 Contributing

We welcome contributions! Please refer to the TypeScript version's guidelines for general principles.

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
