# Implementation Plan: Edit Config Command

**Branch**: `004-edit-config-command` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-edit-config-command/spec.md`

## Summary

Add a `twmcp edit` subcommand that opens the canonical TOML config in the user's editor (`$EDITOR` / `$VISUAL` / `vi`). Include `--init` to bootstrap a commented starter config with overwrite protection. Follows existing CLI patterns (typer command, `--config` option, `_load_config_or_exit` error handling).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: typer >=0.15 (existing), stdlib subprocess/os/shutil
**Storage**: Filesystem (TOML config file at `~/.config/twmcp/config.toml`)
**Testing**: pytest + typer.testing.CliRunner (existing pattern)
**Target Platform**: macOS / Linux (Unix-like)
**Project Type**: single (src layout)
**Performance Goals**: N/A (interactive command, human-speed)
**Constraints**: No new dependencies. Must use stdlib only beyond existing typer.
**Scale/Scope**: Single new CLI command with ~60-80 lines of production code.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First | PASS | Tests written before implementation per TDD |
| II. Simplicity | PASS | Single module addition, no abstractions needed, stdlib only |
| III. CLI Interface | PASS | Text in/out, meaningful errors, non-zero exits, testable via CliRunner |
| Runtime: Python 3.13+ | PASS | No compatibility shims |
| Runtime: Prefer stdlib | PASS | `subprocess.run`, `os.environ`, `shutil.which` — all stdlib |
| Dependencies: Must justify | PASS | No new dependencies added |
| Tooling: ruff, src/ layout | PASS | Follows existing project conventions |
| Testing: 85% coverage | PASS | All paths covered by unit tests |
| Directory Layout | PASS | New file in `src/twmcp/`, tests in `tests/` |

**Gate result: PASS** — no violations, no complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-edit-config-command/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/twmcp/
├── cli.py               # MODIFIED: add `edit` command
├── editor.py            # NEW: editor resolution + init template logic
└── (all other files unchanged)

tests/
├── test_cli.py          # MODIFIED: add TestEditCommand class
└── test_editor.py       # NEW: unit tests for editor.py functions
```

**Structure Decision**: The `edit` command logic splits into two concerns:
1. **CLI wiring** (`cli.py`): The `@app.command()` function — thin, delegates to helpers.
2. **Editor logic** (`editor.py`): Editor resolution, template generation, file creation. Testable without CLI framework overhead.

This matches the existing pattern where `compiler.py`, `config.py`, `selector.py` hold domain logic and `cli.py` wires them together.

## Design Decisions

### D1: Editor resolution function

```
resolve_editor() -> str
```

Returns the editor command string. Precedence: `$EDITOR` > `$VISUAL` > `vi`.
Uses `os.environ.get()` — simple, no edge cases.

### D2: Default config template

A string constant `DEFAULT_CONFIG_TEMPLATE` in `editor.py`. Contains:
- Commented header explaining the file's purpose
- `env_file` setting (commented out)
- Two commented-out example servers: one stdio, one http
- Comments explaining each field

This is a static string, not a generated structure. Keeps things simple and readable.

### D3: Init flow

```
init_config(path: Path) -> None
  - If path exists: raise FileExistsError with helpful message
  - Create parent dirs: path.parent.mkdir(parents=True, exist_ok=True)
  - Write DEFAULT_CONFIG_TEMPLATE to path
```

### D4: Edit flow

```
open_in_editor(path: Path) -> int
  - editor = resolve_editor()
  - result = subprocess.run([editor, str(path)])
  - return result.returncode
```

Uses `subprocess.run` (blocking, inherits stdin/stdout/stderr). The editor gets full terminal control.

### D5: CLI command

```python
@app.command()
def edit(
    config: Path = typer.Option(DEFAULT_CONFIG, help="Path to config file"),
    init: bool = typer.Option(False, "--init", help="Create default config"),
) -> None:
```

Flow:
1. If `--init`: call `init_config(config)`, then open in editor
2. If no `--init` and config doesn't exist: error with suggestion
3. If no `--init` and config exists: open in editor

### D6: Error handling

All errors use `typer.echo()` + `raise typer.Exit(1)` — consistent with existing commands. Specific messages for:
- File exists (during `--init`)
- File not found (without `--init`)
- Editor not found (`shutil.which` check)
- Editor launch failure (subprocess error)

## File Change Summary

| File | Action | Lines (est.) |
|------|--------|-------------|
| `src/twmcp/editor.py` | NEW | ~50 |
| `src/twmcp/cli.py` | MODIFY | ~25 added |
| `tests/test_editor.py` | NEW | ~80 |
| `tests/test_cli.py` | MODIFY | ~60 added |

**Total**: ~215 lines of new/modified code.
