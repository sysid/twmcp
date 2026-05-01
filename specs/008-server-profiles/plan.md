# Implementation Plan: Named Server Profiles

**Branch**: `008-server-profiles` | **Date**: 2026-05-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-server-profiles/spec.md`

## Summary

Add a `[profiles]` TOML table to the canonical config that lets users name
reusable subsets of servers (e.g. `emea = ["aws-mcp-e2e-losnext-emea",
"aws-mcp-e2e-los-emea"]`). Add `--profile <name>` to the `compile` command
to filter the compiled output to a profile's servers, and add a `twmcp
profiles` command for discovery. Behavior without `--profile` is unchanged
(FR-008). `--profile` and `--select` are mutually exclusive; `--profile +
--interactive` pre-seeds the picker. Existing warn-and-skip behavior for
type-incompatible servers is preserved (per clarification).

Implementation is a small surgical extension of three existing layers:
TOML parsing (`config.py`), selection routing (`cli._resolve_selection`),
and a new list command. No new dependencies.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer, stdlib (`tomllib`, `pathlib`, `dataclasses`)
**Storage**: Filesystem — canonical TOML at `~/.config/twmcp/config.toml`
**Testing**: pytest + pytest-cov; CliRunner for typer integration tests
**Target Platform**: Local CLI on macOS/Linux (any platform with Python 3.13+)
**Project Type**: Single project (src layout)
**Performance Goals**: N/A (interactive CLI, sub-second compile)
**Constraints**: No new external dependencies; TOML schema must be additive
**Scale/Scope**: ≤ a few dozen servers, ≤ a few profiles per config

## Constitution Check

| Principle | Compliance | Notes |
|---|---|---|
| I. Test-First (TDD) | PASS | Tasks will follow Red-Green-Refactor; failing tests written first per existing project pattern. |
| II. Simplicity (YAGNI) | PASS | No nesting, no default profile (per clarification A), no new abstractions. Reuses existing `_resolve_selection` plumbing. |
| III. CLI Interface | PASS | Adds `--profile <name>` flag, `twmcp profiles` command, `--json` machine-readable output, stderr for errors, non-zero exit codes on failure. |
| IV. Documentation Completeness | PASS (planned) | README and CLAUDE.md updates scheduled as Polish-phase tasks. specs/ left intact. |

**Runtime constraints**: Python 3.13+ — no shims. Stdlib-only — no new deps.
**Logging**: Reuse existing `-v` debug logging; surface profile resolution
events per FR-010.

No constitution violations. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/008-server-profiles/
├── plan.md              # This file
├── research.md          # Phase 0 — minimal (no open unknowns)
├── data-model.md        # Phase 1 — Profile entity + CanonicalConfig delta
├── quickstart.md        # Phase 1 — user-facing walkthrough
├── contracts/
│   └── cli-behavior.md  # Phase 1 — exact flag semantics + exit codes
├── checklists/
│   └── requirements.md  # From /speckit.specify
└── tasks.md             # Phase 2 — created by /speckit.tasks (not by this command)
```

### Source Code (repository root)

```text
src/twmcp/
├── config.py            # +profiles parser + CanonicalConfig.profiles field
├── selector.py          # +resolve_profile_selection helper
├── cli.py               # +--profile flag on compile; +profiles command
└── (no other files changed)

tests/
├── test_config.py       # +profile parsing/validation tests
├── test_selector.py     # +profile resolution tests (or new file if absent)
├── test_cli.py          # +CLI integration tests for --profile and `profiles` cmd
└── fixtures/
    ├── sample_config_with_profiles.toml   # NEW
    └── (existing fixtures unchanged)
```

**Structure Decision**: Single project, src layout — same as today. No
new top-level modules. Profile parsing slots into `config.py` next to
`_parse_agent_overrides`; profile resolution slots into the existing
`_resolve_selection` flow in `cli.py`.

## Complexity Tracking

No violations. Section intentionally empty.
