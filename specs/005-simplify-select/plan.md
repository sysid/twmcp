# Implementation Plan: Simplify Select Options

**Branch**: `005-simplify-select` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-simplify-select/spec.md`

## Summary

Replace the fragile Click monkey-patching (`_flag_needs_value`, `_apply_select_patch`, `_install_select_patch`) with two clean, separate flags: `--select <value>` for non-interactive server filtering (including `--select none` for empty configuration) and `--interactive` for terminal-based multi-select. This eliminates ~50 lines of patch infrastructure while adding the ability to produce empty configurations — functionality impossible with the current design.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer >=0.15, simple-term-menu (existing — no new deps)
**Storage**: N/A (filesystem config files, unchanged)
**Testing**: pytest + pytest-cov (85% minimum coverage)
**Target Platform**: macOS / Linux CLI
**Project Type**: single
**Performance Goals**: N/A (CLI tool, not performance-sensitive)
**Constraints**: No new dependencies. Must preserve `--select <names>` behavior for existing scripts.
**Scale/Scope**: 2 source files changed, 2 test files updated, ~50 lines removed, ~30 lines added

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First | PASS | TDD: write tests first, verify they fail, then implement |
| II. Simplicity | PASS | This IS a simplification — removing complexity, not adding it |
| III. CLI Interface | PASS | Clear error messages, non-zero exit codes, fail fast |
| Runtime: Python 3.13+ | PASS | No change |
| Runtime: Prefer stdlib | PASS | No new dependencies |
| Tooling: ruff/ty | PASS | Existing linting pipeline applies |
| Testing: 85% coverage | PASS | Tests updated to cover all new paths |
| Directory: src/ layout | PASS | No structural changes |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/005-simplify-select/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (minimal — no unknowns)
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
src/twmcp/
├── cli.py               # MODIFY: remove patch infra, add --interactive, simplify --select
└── selector.py          # MODIFY: update parse_select_value for `none` keyword

tests/
├── test_cli.py          # MODIFY: update interactive tests (--select → --interactive), add new tests
└── test_selector.py     # MODIFY: add tests for `none` keyword handling
```

**Structure Decision**: No new files. Pure refactoring of existing `cli.py` and `selector.py` with corresponding test updates.

## Phase 0: Research

No NEEDS CLARIFICATION items in Technical Context. All decisions resolved during `/speckit.clarify`. Research is trivial — documented below for completeness.

### R-001: Typer Option[str] behavior with empty strings

- **Decision**: `--select ""` passes empty string to the callback. Typer/Click does not strip it.
- **Rationale**: Verified in existing codebase — `parse_select_value("")` currently raises `ValueError`. We keep this behavior and enhance the error message to suggest `--select none`.
- **Alternatives considered**: Making `--select` a `flag_value` option again (rejected: that's what we're removing).

### R-002: Reserved keyword approach for empty selection

- **Decision**: `none` (case-sensitive) is a reserved keyword in `parse_select_value`.
- **Rationale**: Shell-safe, explicit, readable. Clarified during `/speckit.clarify` session.
- **Alternatives considered**: `--select ""` (shell-fragile), `--no-servers` flag (too many flags).

## Phase 1: Design

### Changes to `selector.py`

**`parse_select_value(value: str) -> list[str]`** — Current behavior plus:

1. If `value` is `"none"` (exact match, case-sensitive), return `[]` immediately.
2. After splitting and stripping, if any element is `"none"` mixed with other names, raise `ValueError`: `"'none' is a reserved keyword and cannot be combined with server names. Use --select none alone for empty configuration."`
3. Empty string / whitespace-only continue to raise `ValueError` with updated message: `"No server names provided. Use --select none for empty configuration."`

No changes to `validate_server_names` or `select_servers_interactive`.

### Changes to `cli.py`

**Remove entirely:**
- `_INTERACTIVE` sentinel constant (line 22)
- `_apply_select_patch()` function (lines 231-244)
- `_install_select_patch()` function (lines 247-275)
- `_install_select_patch()` call at module level (line 278)
- `import click` (line 6) — no longer needed

**Modify `compile()` command signature:**
- `select: Optional[str]` — unchanged (standard typer Option, no patch needed)
- Add `interactive: bool = typer.Option(False, "--interactive", help="Interactive server selection via terminal menu")`

**Modify `_resolve_selection()`:**
- Change signature to `_resolve_selection(select: str | None, interactive: bool, canonical: CanonicalConfig) -> CanonicalConfig`
- Add mutual exclusivity check: if both `select is not None` and `interactive`, error + exit 1
- If `interactive`:
  - Check `is_interactive_terminal()`, error if not
  - Call `select_servers_interactive()`
  - Handle None (cancelled) → exit 0
  - Handle empty list → empty config
- If `select is not None`:
  - Call `parse_select_value(select)` (handles `none` keyword, empty string errors)
  - Call `validate_server_names()` if names returned
- If neither → return canonical unchanged

### Test Changes

**`test_selector.py`** — Add to `TestParseSelectValue`:
- `test_none_keyword_returns_empty_list`: `parse_select_value("none")` → `[]`
- `test_none_mixed_with_names_raises`: `parse_select_value("none,github")` → `ValueError`
- `test_none_case_sensitive`: `parse_select_value("None")` → `["None"]` (not treated as keyword)
- `test_empty_string_error_suggests_none`: verify error message contains "--select none"

**`test_cli.py`** — `TestCompileSelectInteractive`:
- Change all `--select` (bare) to `--interactive` in test invocations
- Remove Click patch-dependent test assumptions

**`test_cli.py`** — Add `TestCompileSelectNone` class:
- `test_select_none_produces_empty_config`: `--select none` → `{"mcpServers": {}}`
- `test_select_none_with_all`: `--all --select none` → all agents empty
- `test_select_empty_string_exits_1`: `--select ""` → exit 1 with suggestion
- `test_select_whitespace_exits_1`: `--select " , "` → exit 1

**`test_cli.py`** — Add `TestCompileSelectInteractiveMutualExclusivity`:
- `test_select_and_interactive_exits_1`: both flags → exit 1

## Complexity Tracking

No constitution violations. No complexity tracking needed.
