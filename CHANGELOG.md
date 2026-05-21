# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-21

Ports lemura v1.4.4 features to pylemura.

### Added

- **`StepVerifier` / `StepVerifierResult`** — attach a semantic verifier to any `ContinuationStep`
  to inspect the tool output after execution and return a `pass`, `fail`, or `retry` verdict.
  Supports async `check` functions and a configurable `max_retries` count before a `retry` verdict
  is forced to `failed`.
- **`ContinuationStep.verify`** field — optional `StepVerifier` attached to a step.
- **`ContinuationPlanner.mark_step_pending(step_id)`** — resets a step to `pending` for a retry
  attempt and increments the internal retry counter.
- **`ContinuationPlanner.get_retry_count(step_id) -> int`** — returns how many times a step has
  been retried.
- **`ContinuationPlanner` callbacks** — `on_step_failed` and `on_step_skipped` constructor
  arguments; fired on every direct and transitively propagated status change.
- **`SessionManager.get_plan()`** — returns a snapshot of the current continuation plan after
  `set_plan()` / `run()`, or `None` if no plan is set. Useful for post-run inspection of step
  statuses.
- **`TraceEvent` type `"verification"`** — emitted when a step verifier returns `fail` or `retry`.
- **`set_plan()` now stores the plan in `context.metadata["continuationPlan"]`** so it survives
  context compression, matching the lemura TS behaviour.
- **`_run_single_tool` now calls `mark_step_running` / `mark_step_done`** — continuation plan step
  statuses are now correctly updated during tool execution (these were missing in prior versions).

### Changed

- **`SessionConfig.max_completion_tokens` default raised from `2 000` to `4 000`** — matches
  lemura v1.4.4. Existing configs that set this explicitly are unaffected.
- **`mark_step_failed(step_id, reason)` and `mark_step_skipped(step_id, reason)`** now accept an
  optional `reason` string (default: `"step failed"` / `"condition not met"`). The reason is
  forwarded to the registered callback and included in propagated-skip messages.

### Fixed

- `mark_step_running` and `mark_step_done` were never called during tool execution, so the
  continuation plan step statuses were never updated. Both calls are now correctly placed in
  `_run_single_tool`.

## [1.1.0] - 2026-03-29

### Fixed
- Restored Python 3.11 compatibility by removing logger f-string expressions that triggered an import-time `SyntaxError`.
- Unblocked Docker deployments that passed environment variables correctly but failed while importing `pylemura`.

### Added
- Added a regression test covering logger metadata rendering for the Python 3.11 compatibility fix.

## [1.0.0] - 2026-03-29

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
