# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-15

### Added
- Initial release of `pylemura`.
- Complete ReAct (Reasoning + Acting) loop orchestration system.
- Provider-agnostic adapter for OpenAI-compatible endpoints.
- Context management with Sandwich, History, and Summary injection strategies.
- Skill marketplace for fixed and dynamic skills.
- Tool registry with JSON Schema validation and parallel execution.
- Model Context Protocol (MCP) support.
- Media Bridge for ASR, TTS, vision, and image generation.
- Short-term memory (STM) with chunked storage.
- RAG support with in-memory adapter.
- Zero-dependency core (stdlib only).
