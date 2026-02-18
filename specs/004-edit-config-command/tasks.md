# Tasks: Edit Config Command

**Input**: Design documents from `/specs/004-edit-config-command/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: Included — constitution mandates TDD (Test-First is NON-NEGOTIABLE).

**Organization**: Tasks grouped by user story. US2 and US3 share `init_config()` — US3 adds the error path.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create new module files with minimal scaffolding

- [x] T001 [P] Create `src/twmcp/editor.py` with module docstring and imports (os, shlex, shutil, subprocess, pathlib.Path)
- [x] T002 [P] Create `tests/test_editor.py` with imports (pytest, from twmcp.editor import ...)

**Checkpoint**: Both files exist, `make test` still passes (no new tests yet)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Write tests for `resolve_editor()` in `tests/test_editor.py::TestResolveEditor` — cases: EDITOR set, VISUAL fallback, vi default, EDITOR with args via shlex.split (e.g., "code --wait")
- [x] T004 Implement `resolve_editor()` in `src/twmcp/editor.py` — returns `(cmd, args)` tuple, precedence: $EDITOR > $VISUAL > "vi"

**Checkpoint**: `uv run python -m pytest tests/test_editor.py::TestResolveEditor -v` all green

---

## Phase 3: User Story 1 — Open Config in Editor (Priority: P1) MVP

**Goal**: `twmcp edit` opens the canonical config in the user's preferred editor

**Independent Test**: Run `twmcp edit --config <existing-file>` and verify editor is launched with correct path

### Tests for User Story 1

> **Write these tests FIRST, ensure they FAIL before implementation**

- [x] T005 [P] [US1] Write tests for `open_in_editor()` in `tests/test_editor.py::TestOpenInEditor` — cases: calls subprocess.run with correct cmd+args+path, returns exit code, raises error when editor not found (shutil.which returns None)
- [x] T006 [P] [US1] Write CLI tests for basic `edit` in `tests/test_cli.py::TestEditCommand` — cases: edit opens editor with config path, edit with --config uses custom path, edit without existing config exits 1 with "twmcp edit --init" suggestion

### Implementation for User Story 1

- [x] T007 [US1] Implement `open_in_editor(path: Path) -> int` in `src/twmcp/editor.py` — resolve editor, validate with shutil.which, subprocess.run with inherited stdio
- [x] T008 [US1] Add `edit` command to `src/twmcp/cli.py` — basic flow: config exists → open_in_editor, config missing → error with --init suggestion. Import from editor.py, use DEFAULT_CONFIG and --config option consistent with compile command

**Checkpoint**: `uv run python -m pytest tests/test_editor.py::TestOpenInEditor tests/test_cli.py::TestEditCommand -v` all green. US1 is independently functional.

---

## Phase 4: User Story 2 — Initialize New Config (Priority: P1)

**Goal**: `twmcp edit --init` creates a commented starter config and opens it in the editor

**Independent Test**: Run `twmcp edit --init --config <new-path>` in clean directory, verify file created with valid TOML content and editor launched

**Depends on**: US1 (edit command must exist to add --init flag)

### Tests for User Story 2

> **Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US2] Write tests for `DEFAULT_CONFIG_TEMPLATE` in `tests/test_editor.py::TestDefaultTemplate` — template is valid TOML (tomllib.loads), contains commented example servers, contains env_file reference
- [x] T010 [P] [US2] Write tests for `init_config()` in `tests/test_editor.py::TestInitConfig` — cases: creates file with template content at given path, creates parent directories when missing (tmp_path)
- [x] T011 [US2] Write CLI tests for `edit --init` in `tests/test_cli.py::TestEditCommand` — cases: --init creates config then opens editor, --init with --config uses custom path, --init creates parent dirs

### Implementation for User Story 2

- [x] T012 [US2] Add `DEFAULT_CONFIG_TEMPLATE` string constant in `src/twmcp/editor.py` — commented TOML with: header comment, env_file (commented), example stdio server (commented), example http server (commented)
- [x] T013 [US2] Implement `init_config(path: Path) -> None` in `src/twmcp/editor.py` — mkdir parents, write template to path
- [x] T014 [US2] Add `--init` flag to `edit` command in `src/twmcp/cli.py` — flow: init_config(path) then open_in_editor(path)

**Checkpoint**: `uv run python -m pytest tests/test_editor.py::TestDefaultTemplate tests/test_editor.py::TestInitConfig tests/test_cli.py::TestEditCommand -v` all green. US2 independently functional.

---

## Phase 5: User Story 3 — Protect Existing Config from Overwrite (Priority: P1)

**Goal**: `twmcp edit --init` refuses to overwrite an existing config, exits with helpful error

**Independent Test**: Create a file, run `twmcp edit --init --config <that-file>`, verify exit code 1 and error message mentioning "already exists" and suggesting `twmcp edit`

**Depends on**: US2 (init_config must exist to add the guard)

### Tests for User Story 3

> **Write these tests FIRST, ensure they FAIL before implementation**

- [x] T015 [P] [US3] Write tests for overwrite protection in `tests/test_editor.py::TestInitConfig` — case: init_config raises FileExistsError when path already exists, file content unchanged after failed call
- [x] T016 [P] [US3] Write CLI tests for overwrite protection in `tests/test_cli.py::TestEditCommand` — cases: --init with existing config exits 1, error message contains "already exists", error message suggests "twmcp edit" (without --init), file content unchanged

### Implementation for User Story 3

- [x] T017 [US3] Add existence check to `init_config()` in `src/twmcp/editor.py` — if path.exists(): raise FileExistsError with descriptive message
- [x] T018 [US3] Add FileExistsError handling to `edit` command in `src/twmcp/cli.py` — catch FileExistsError, echo error with suggestion, raise typer.Exit(1)

**Checkpoint**: `uv run python -m pytest tests/test_editor.py::TestInitConfig tests/test_cli.py::TestEditCommand -v` all green. Overwrite protection verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [x] T019 Run full test suite: `make test` — verify all tests pass and coverage >= 85%
- [x] T020 Run `make format` and `make lint` — ensure ruff compliance

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ──→ Phase 2 (Foundational) ──→ Phase 3 (US1) ──→ Phase 4 (US2) ──→ Phase 5 (US3) ──→ Phase 6 (Polish)
```

### User Story Dependencies

- **US1**: Depends on Foundational (resolve_editor). No dependencies on other stories.
- **US2**: Depends on US1 (edit command must exist to add --init). Depends on Foundational.
- **US3**: Depends on US2 (init_config must exist to add guard). Overwrite protection is the error path of init.

**Note**: US2 and US3 are tightly coupled — US3 adds the guard clause to US2's `init_config()`. They are sequential, not parallelizable.

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. editor.py functions before cli.py wiring
3. Core implementation before error handling

### Parallel Opportunities

- T001 + T002: Both file creation, no dependencies
- T005 + T006: Different test files (editor vs CLI tests for US1)
- T009 + T010: Different test classes within same file (template vs init)
- T015 + T016: Different test files (editor vs CLI overwrite tests)

---

## Parallel Example: User Story 1

```bash
# Write tests in parallel (different files):
Task T005: "Write open_in_editor tests in tests/test_editor.py"
Task T006: "Write CLI edit tests in tests/test_cli.py"

# Then implement sequentially (CLI depends on editor.py):
Task T007: "Implement open_in_editor in src/twmcp/editor.py"
Task T008: "Add edit command to src/twmcp/cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T004)
3. Complete Phase 3: User Story 1 (T005-T008)
4. **STOP and VALIDATE**: `twmcp edit --config <file>` opens editor
5. Functional but no `--init` yet

### Incremental Delivery

1. Setup + Foundational → resolve_editor works
2. Add US1 → `twmcp edit` opens editor → **MVP!**
3. Add US2 → `twmcp edit --init` bootstraps config
4. Add US3 → Overwrite protection added
5. Polish → Full test suite, formatting, linting

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- All stories are P1 but have natural ordering: edit → init → protect
- US3 is the error path of US2 — cannot be implemented independently
- Commit after each phase checkpoint
- `make test` after every implementation task to catch regressions
