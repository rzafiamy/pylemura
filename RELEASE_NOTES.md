# Release Notes - v1.0.0

## 🚀 Welcome to pylemura v1.0.0!

We are thrilled to announce the first stable release of `pylemura`, the official Python portage of the [lemura](https://github.com/rzafiamy/lemura) agentic runtime. `pylemura` brings a premium, robust, and provider-agnostic framework for building sophisticated AI agents in Python.

---

### 🌟 Key Features

- **🧠 Complete ReAct Orchestration**: A robust Reasoning + Acting loop that manages tool calls, context, and goal maintenance out of the box.
- **🧩 Dynamic Skill Market**: A powerful system to load and unload agent skills (tools + prompts) based on tags, names, or dependencies.
- **🔌 Provider Agnostic**: Native support for OpenAI-compatible endpoints, allowing you to switch between OpenAI, Groq, Together, Ollama, and more with zero code changes.
- **🛡️ Integrated Tool Firewall**: A security-first approach with built-in ask/accept/deny policies for sensitive tool executions.
- **⚡ Parallel Tool Execution**: Significantly reduce latency by executing independent tool calls concurrently.
- **🧹 Advanced Context Management**: Intelligent strategies for context compression, including "Summary Injection" to maintain long-term coherence.
- **🔌 Model Context Protocol (MCP)**: First-class support for MCP, enabling easy integration with a vast ecosystem of external tools.
- **📦 Zero-Dependency Core**: The entire runtime is built using the Python standard library, ensuring maximum compatibility and minimal overhead.

---

### 📦 What's New

#### Core Runtime
- Implementation of the `ReAct` loop with continuation planning.
- `SessionManager` for high-level interaction.
- `ContextManager` with multiple injection and compression strategies.

#### Tooling & Skills
- `ToolRegistry` with strict JSON Schema validation.
- support for `Skills` (YAML/Markdown definitions of tools and system instructions).
- Parallel execution engine for tool calls.

#### Memory & RAG
- Short-term memory (STM) with chunked storage.
- In-memory RAG adapter for document-based retrieval.

#### Multimedia
- `MediaBridge` for ASR (Speech-to-Text), TTS (Text-to-Speech), Vision, and Image Generation.

---

### 📝 Getting Started

Install the latest version via pip:

```bash
pip install pylemura
```

Check out the [Quick Start guide](https://github.com/rzafiamy/pylemura#quick-start) in the README or visit our [documentation](https://lemura.makix.fr).

---

### 🤝 Transitions
This release marks the transition from beta to stable. We have unified the API to match the TypeScript core while optimizing for Python's asynchronous patterns.

---

*Thank you to all the contributors and early testers who helped make this possible!*
