# Implementation Plan: Project-Local Agent Configurations

**Branch**: `006-local-agent-configs` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-local-agent-configs/spec.md`

## Summary

Add a `claude-code` agent profile and change `copilot-cli` to use project-local config paths (relative to CWD) instead of global paths. The claude-code profile uses `mcpServers` key, includes `type` field, flat headers, and supports all server types (stdio, http, sse). The copilot-cli change is a path-only change — its JSON format stays identical.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer (CLI), stdlib (pathlib, json, dataclasses)
**Storage**: Filesystem (JSON config files)
**Testing**: pytest + pytest-cov (85% minimum)
**Target Platform**: macOS/Linux CLI
**Project Type**: single
**Performance Goals**: N/A (CLI tool, instant execution)
**Constraints**: No new dependencies. Relative paths resolved at compile time.
**Scale/Scope**: 2 files changed (agents.py, test_agents.py), plus test_compiler.py updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First | PASS | Tests updated before/alongside implementation |
| II. Simplicity | PASS | Minimal change: 1 new registry entry + 1 path change |
| III. CLI Interface | PASS | No CLI interface change — existing `compile` command works with new agent name |
| IV. Documentation Completeness | PASS | CLAUDE.md and README.md to be updated post-implementation |

No violations. Gate passed.

## Project Structure

### Documentation (this feature)

```text
specs/006-local-agent-configs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/twmcp/
├── agents.py            # MODIFY: add claude-code profile, change copilot-cli path
├── compiler.py          # NO CHANGE (already handles all header_style/type_mapping combos)
├── cli.py               # NO CHANGE (already handles any registered agent)

tests/
├── test_agents.py       # MODIFY: add claude-code tests, update copilot-cli path assertions, update count
├── test_compiler.py     # MODIFY: add claude-code transform tests
```

**Structure Decision**: Existing `src/` layout. No new files or directories needed — only modifications to existing modules and tests.

## Complexity Tracking

No violations to justify.
