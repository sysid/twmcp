# Implementation Plan: Configurable Agent Output Paths

**Branch**: `007-configurable-config-paths` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-configurable-config-paths/spec.md`

## Summary

Let users override each agent's hard-coded MCP output path from `~/.config/twmcp/config.toml` via a new optional `[agents.<name>]` section with a `config_path` string field. Overrides flow through the existing TOML loader (so `${VAR}` and `~` interpolation work for free) and are applied wherever code consumes `AgentProfile.config_path` — namely `compile`, `compile --all`, and `agents`. `twmcp edit --init` generates a commented `[agents.*]` block seeded from the registry so users discover the mechanism without reading source.

Technical approach: extend `CanonicalConfig` with an `agent_overrides: dict[str, str]` field parsed from `[agents.*]`; validate keys against `AGENT_REGISTRY` at load time; resolve each profile's effective path by merging the override onto the built-in default, expanding `~`. The registry itself stays immutable (frozen dataclass) — we derive resolved profiles per invocation.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer ≥ 0.15 (CLI), stdlib (tomllib, pathlib, os)
**Storage**: Filesystem — canonical TOML at `~/.config/twmcp/config.toml`; JSON outputs at per-agent paths (now overridable)
**Testing**: pytest + pytest-cov; ≥ 85% coverage (constitution)
**Target Platform**: macOS, Linux (any filesystem `twmcp` already runs on)
**Project Type**: single (src-layout Python CLI)
**Performance Goals**: n/a — one-shot CLI invocation, dominated by file I/O
**Constraints**: Fully backwards compatible. Absence of `[agents]` section MUST change nothing.
**Scale/Scope**: 4 registered agents today, any future additions covered by the same mechanism.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Test-First | PASS | Every new behavior (override parsing, validation, path expansion, `edit --init` output, effective path in `agents`) gets a failing test first. |
| II. Simplicity | PASS | No new abstractions. Extends existing `CanonicalConfig` dataclass with one field; resolution is a pure function on the registry + overrides dict. No registry mutation, no side-effectful state. |
| III. CLI Interface | PASS | No new commands. Existing `--json` output on `agents` reflects the effective path naturally. Errors stay on stderr with non-zero exit. |
| IV. Documentation Completeness | PASS (tracked) | CLAUDE.md "Active Technologies" + "Recent Changes", README.md "CLI Reference" / TOML schema section, and `twmcp edit --init` template all updated as part of implementation tasks. |

No violations. Complexity Tracking section below is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/007-configurable-config-paths/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── config-schema.md # TOML schema for [agents.*] + validation rules
│   └── cli-behavior.md  # CLI-level behavior contract (edit --init, compile, agents)
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # /speckit.tasks output (not created here)
```

### Source Code (repository root)

```text
src/twmcp/
├── agents.py        # AGENT_REGISTRY (unchanged); NEW helper: resolve_profile(name, overrides) -> AgentProfile
├── config.py        # Extend CanonicalConfig with agent_overrides; parse [agents.*]; validate keys/types
├── editor.py        # Extend DEFAULT_CONFIG_TEMPLATE with commented [agents.*] block generated from AGENT_REGISTRY
├── compiler.py      # write_config unchanged; callers pass resolved path
└── cli.py           # compile/compile --all/agents: resolve profile via overrides before use

tests/
├── test_config.py        # NEW cases: [agents.*] parsing, ${VAR}/~ expansion in config_path, unknown-agent error, non-string error, empty/missing section
├── test_agents.py        # NEW: resolve_profile() unit tests
├── test_editor.py        # NEW file: init_config seeds expected commented block for every registered agent
├── test_cli.py           # NEW: compile uses override path, agents shows effective path (text + --json)
└── fixtures/
    ├── sample_config_with_overrides.toml     # NEW
    └── expected/
        └── agents_with_overrides.json        # NEW (for agents --json assertion)
```

**Structure Decision**: Single-project src-layout Python package, consistent with the existing codebase. No new top-level modules — the feature is additive inside `config.py`, `agents.py`, `editor.py`, and `cli.py`.

## Complexity Tracking

> No violations — section intentionally empty.
