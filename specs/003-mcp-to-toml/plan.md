# Implementation Plan: MCP Config to TOML Extractor

**Branch**: `003-mcp-to-toml` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-mcp-to-toml/spec.md`

## Summary

Add `twmcp extract <file>` command that reads an MCP JSON configuration file (Claude Desktop, VS Code, IntelliJ formats), auto-detects its structure, and prints the equivalent twmcp canonical TOML to stdout. Secret values are replaced with `${VAR_NAME}` placeholders. Unknown JSON properties are preserved as TOML comments. No new external dependencies — TOML output is generated via manual string formatting since we need comment support.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer (existing), stdlib only (json, pathlib, re)
**Storage**: N/A (stdin→stdout transform, no persistence)
**Testing**: pytest + pytest-cov (existing)
**Target Platform**: CLI tool (macOS/Linux)
**Project Type**: Single project (existing src/ layout)
**Performance Goals**: N/A (single-file transform, trivially fast)
**Constraints**: No new external dependencies (TOML writing via manual formatting)
**Scale/Scope**: Single JSON file → single TOML output

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Requirement | Status |
|------|-------------|--------|
| I. Test-First | TDD: tests first, red-green-refactor | PASS — plan includes test-first workflow |
| II. Simplicity | YAGNI, minimal changes, no premature abstractions | PASS — single new module + CLI command, no abstractions |
| III. CLI Interface | stdout for output, stderr for errors, non-zero exit on failure | PASS — spec aligns exactly |
| III. CLI Interface | Support human-readable and structured output | PASS — TOML IS the structured output; human-readable by nature |
| III. CLI Interface | Independently testable via subprocess | PASS — CLI test via typer test runner + subprocess |
| Runtime | Prefer stdlib, justify external deps | PASS — no new dependencies |
| Tooling | uv run prefix for all invocations | PASS — existing Makefile pattern |
| Testing | 85% coverage minimum | PASS — all new code will have tests |

No violations. Complexity Tracking section not needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-mcp-to-toml/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: design decisions
├── data-model.md        # Phase 1: input/output data model
├── quickstart.md        # Phase 1: usage guide
├── contracts/           # Phase 1: CLI interface contract
│   └── cli-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/twmcp/
├── __init__.py          # (existing)
├── cli.py               # MODIFIED: add extract command
├── config.py            # (existing, unchanged)
├── agents.py            # (existing, unchanged)
├── compiler.py          # (existing, unchanged)
├── interpolate.py       # (existing, unchanged)
└── extractor.py         # NEW: JSON→TOML extraction logic

tests/
├── conftest.py          # (existing)
├── test_extractor.py    # NEW: extractor unit tests
├── test_cli.py          # MODIFIED: add extract CLI tests
└── fixtures/
    ├── sample_config.toml        # (existing)
    ├── secrets.env               # (existing)
    ├── claude_desktop.json       # NEW: Claude Desktop format fixture
    ├── vscode_mcp.json           # NEW: VS Code format fixture
    ├── flat_servers.json         # NEW: flat format fixture
    ├── with_secrets.json         # NEW: JSON with literal secret values
    ├── with_unknown_props.json   # NEW: JSON with extra properties
    └── expected/
```

**Structure Decision**: Single project, existing `src/` layout. One new module `extractor.py` keeps extraction logic isolated from the existing compilation pipeline. The CLI entry point in `cli.py` gets one new command.
