# Implementation Plan: Interactive MCP Server Selection

**Branch**: `002-interactive-server-select` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-interactive-server-select/spec.md`

## Summary

Add a `--select` flag to the `twmcp compile` command that enables interactive multi-select or non-interactive comma-separated server filtering. Uses a Click parameter patch for dual-mode flag behavior and `simple-term-menu` for the interactive prompt. All changes contained in `cli.py` (modified) and `selector.py` (new).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer >=0.15 (existing), simple-term-menu (new — zero transitive deps)
**Storage**: N/A
**Testing**: pytest + pytest-cov (existing)
**Target Platform**: macOS (Linux compatible)
**Project Type**: Single CLI project (src/ layout)
**Performance Goals**: Selection prompt renders instantly for ≤20 servers
**Constraints**: Must not break existing CLI behavior. New dependency must be justified per constitution.
**Scale/Scope**: ~150 lines new code, 2 files modified, 1 file created, ~200 lines new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First | PASS | TDD cycle: write tests first for selector and CLI, verify fail, then implement. |
| II. Simplicity | PASS | Minimal changes: 1 new module, 1 modified module, 1 new dep with zero transitive deps. No abstractions beyond a simple function. |
| III. CLI Interface | PASS | `--select` follows text in/out protocol. Interactive mode uses stderr for prompt, stdout for JSON. Non-interactive mode is fully scriptable. Fail-fast with non-zero exit on invalid names. |
| Prefer stdlib | PASS | `simple-term-menu` justified: zero deps, no stdlib equivalent for terminal multi-select. |
| Fail fast | PASS | Invalid server names reported immediately with available names listed. Non-TTY detection on bare `--select`. |

**Post-Phase 1 Re-check**:

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First | PASS | Test plan covers: interactive mode (mocked), non-interactive filter, validation errors, backward compat. |
| II. Simplicity | PASS | `selector.py` is ~50 lines (prompt + validation). CLI changes are ~30 lines. No new abstractions. |
| III. CLI Interface | PASS | Contract defined in `contracts/cli-contract.md`. Exit codes documented. |
| Private API usage | JUSTIFIED | Click `_flag_needs_value` patch required due to Click #3084 regression + Typer flag_value removal. Documented, contained, removable when Click fixes ship. See [research.md](research.md). |

## Project Structure

### Documentation (this feature)

```text
specs/002-interactive-server-select/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity relationships
├── quickstart.md        # Phase 1: usage guide
├── contracts/
│   └── cli-contract.md  # Phase 1: CLI behavior contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/twmcp/
├── __init__.py          # (unchanged)
├── cli.py               # MODIFIED: add --select option + Click patch + selection flow
├── selector.py          # NEW: interactive prompt + name validation
├── config.py            # (unchanged)
├── compiler.py          # (unchanged)
├── agents.py            # (unchanged)
└── interpolate.py       # (unchanged)

tests/
├── conftest.py          # (unchanged)
├── test_cli.py          # MODIFIED: add --select test cases
├── test_selector.py     # NEW: unit tests for selector module
└── fixtures/
    └── sample_config.toml  # (unchanged)
```

**Structure Decision**: Existing single-project src/ layout. One new module `selector.py` in `src/twmcp/`. No new directories needed. Follows established pattern of small focused modules (cf. `interpolate.py`, `agents.py`).

## Design Details

### Module: `src/twmcp/selector.py`

Responsibilities:
1. Present interactive multi-select prompt using `simple-term-menu`
2. Validate a set of server names against canonical config
3. TTY detection

```
┌─────────────────────────────────────────────┐
│ selector.py                                  │
│                                              │
│ select_servers_interactive(                   │
│   servers: dict[str, Server]                 │
│ ) -> list[str] | None                        │
│   - Shows multi-select prompt                │
│   - Returns selected server names            │
│   - Returns None on cancel                   │
│                                              │
│ validate_server_names(                        │
│   names: list[str],                          │
│   available: dict[str, Server]               │
│ ) -> list[str]                               │
│   - Validates all names exist                │
│   - Raises ValueError with unrecognized names│
│                                              │
│ parse_select_value(                           │
│   value: str                                 │
│ ) -> list[str]                               │
│   - Splits comma-separated string            │
│   - Strips whitespace, filters empty         │
│                                              │
│ is_interactive_terminal() -> bool            │
│   - Checks sys.stdin.isatty()                │
└─────────────────────────────────────────────┘
```

### Module: `src/twmcp/cli.py` (changes)

1. Add `select: Optional[str]` parameter to `compile` command
2. Module-level `_patch_select_option()` to enable dual-mode flag
3. Selection flow inserted between config loading and compilation:

```
compile() entry
    │
    ├─ select is None → existing behavior (all servers)
    │
    ├─ select is _INTERACTIVE
    │   ├─ not TTY? → error + exit 1
    │   ├─ show prompt → user selects
    │   │   ├─ cancelled? → exit 0
    │   │   ├─ empty? → info message + exit 0
    │   │   └─ names selected → filter config.servers
    │
    └─ select is "name1,name2"
        ├─ parse names
        ├─ validate against config → unknown? error + exit 1
        └─ filter config.servers
    │
    ▼
existing compile flow (single agent or --all)
```

### Filtering Approach

Server filtering is applied by creating a filtered copy of `CanonicalConfig`:

```python
# Simple dict comprehension — no new abstraction needed
filtered_servers = {k: v for k, v in canonical.servers.items() if k in selected_names}
filtered_config = CanonicalConfig(servers=filtered_servers, env_file=canonical.env_file)
```

This filtered config is then passed to the existing `_compile_single` / `_compile_all` functions unchanged.

### Click Patch for Dual-Mode `--select`

```python
_INTERACTIVE = "__interactive__"

def _patch_select_option() -> None:
    """Patch --select to support optional values.

    Workaround for Click #3084 regression and Typer's removal of flag_value.
    """
    click_app = typer.main.get_command(app)
    cmd = click_app.commands.get("compile") if isinstance(click_app, click.Group) else click_app
    if cmd is None:
        return
    for param in cmd.params:
        if isinstance(param, click.Option) and param.name == "select":
            param._flag_needs_value = True
            param.flag_value = _INTERACTIVE
            return

_patch_select_option()  # runs once at module import
```

## Complexity Tracking

| Item | Justification | Simpler Alternative Rejected Because |
|------|--------------|-------------------------------------|
| Click `_flag_needs_value` patch | Click #3084 regression blocks native approach. Typer removed `flag_value`. | Two separate flags rejected by spec clarification (Tom chose dual-mode). |
| `simple-term-menu` dependency | Zero-dep package for terminal multi-select | DIY with Rich requires ~100 LOC of fragile raw terminal code. No stdlib multi-select exists. |
