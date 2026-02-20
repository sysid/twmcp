# Tasks: Simplify Select Options

**Input**: Design documents from `/specs/005-simplify-select/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: Included — TDD is mandatory per project constitution.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

## Phase 1: Foundational — selector.py `none` Keyword

**Purpose**: Add `none` reserved keyword support to `parse_select_value()`. This is the foundation enabling US2 (empty selection) at the CLI level.

### Tests

- [x] T001 [P] Write test `test_none_keyword_returns_empty_list` in tests/test_selector.py — `parse_select_value("none")` returns `[]`
- [x] T002 [P] Write test `test_none_mixed_with_names_raises` in tests/test_selector.py — `parse_select_value("none,github")` raises `ValueError` mentioning reserved keyword
- [x] T003 [P] Write test `test_none_case_sensitive` in tests/test_selector.py — `parse_select_value("None")` returns `["None"]` (not treated as keyword)
- [x] T004 [P] Write test `test_empty_string_error_suggests_none` in tests/test_selector.py — error message from `parse_select_value("")` contains `--select none`

### Implementation

- [x] T005 Update `parse_select_value()` in src/twmcp/selector.py: early return `[]` for `"none"`, reject `none` mixed with names, update empty-string error message to suggest `--select none`

**Checkpoint**: T001-T004 must FAIL before T005. After T005, all selector tests pass.

---

## Phase 2: US1+US2 — Non-Interactive --select with `none` (Priority: P1)

**Goal**: `--select <names>` continues working (US1 regression), `--select none` produces empty config (US2 new), `--select ""` gives helpful error.

**Independent Test**: `twmcp compile copilot-cli --select none --dry-run` outputs `{"mcpServers": {}}`.

### Tests

- [x] T006 [P] [US2] Write test `test_select_none_produces_empty_config` in tests/test_cli.py (TestCompileSelectNone class) — `--select none --dry-run` → `{"mcpServers": {}}`
- [x] T007 [P] [US2] Write test `test_select_none_with_all` in tests/test_cli.py — `--all --select none --dry-run` → all agents have empty server maps
- [x] T008 [P] [US2] Write test `test_select_empty_string_exits_1` in tests/test_cli.py — `--select ""` → exit 1, output contains `--select none`
- [x] T009 [P] [US2] Write test `test_select_whitespace_exits_1` in tests/test_cli.py — `--select " , "` → exit 1

### Implementation

- [x] T010 [US1] Verify all existing `TestCompileSelectNonInteractive` tests still pass (regression check, no code changes needed)
- [x] T011 [US2] No code changes needed — existing `_resolve_selection()` already handles empty list from `parse_select_value()` correctly

**Checkpoint**: T006-T009 must FAIL before T011. After T011, US1 and US2 CLI tests all pass.

---

## Phase 3: US3+US5 — --interactive Flag + Remove Monkey-Patch (Priority: P1/P2)

**Goal**: Replace bare `--select` with `--interactive` flag (US3). Remove all monkey-patch infrastructure (US5). This is one phase because they are deeply coupled — adding `--interactive` makes the patch infrastructure dead code.

**Independent Test**: `twmcp compile copilot-cli --interactive --dry-run` (mocked) shows multi-select menu.

### Tests

- [x] T012 [US3] Update `TestCompileSelectInteractive` in tests/test_cli.py: change all bare `--select` to `--interactive` in test invocations (4 tests: `test_select_bare_calls_interactive`, `test_select_cancelled_exits_0`, `test_select_empty_produces_empty_config`, `test_select_non_tty_exits_1`)
- [x] T013 [US3] Update `TestCompileSelectWithAll` in tests/test_cli.py: change bare `--select` to `--interactive` in interactive test invocations (2 tests: `test_all_select_interactive_called_once`, `test_all_select_interactive_filters_all_agents`)
- [x] T014 [US3] Rename test methods and class names to reflect `--interactive` naming (e.g., `TestCompileInteractive`, `test_interactive_calls_menu`)

### Implementation

- [x] T015 [US3] Add `interactive: bool = typer.Option(False, "--interactive", help="Interactive server selection via terminal menu")` parameter to `compile()` in src/twmcp/cli.py
- [x] T016 [US3] Update `_resolve_selection()` signature in src/twmcp/cli.py: add `interactive: bool` parameter, route interactive=True to `select_servers_interactive()` path
- [x] T017 [US5] Remove `_INTERACTIVE` sentinel, `_apply_select_patch()`, `_install_select_patch()`, module-level `_install_select_patch()` call, and `import click` from src/twmcp/cli.py

**Checkpoint**: T012-T013 will cause test failures (bare `--select` no longer works as flag). After T015-T017, all tests pass. No monkey-patch code remains.

---

## Phase 4: US4 — Mutual Exclusivity (Priority: P2)

**Goal**: `--select` and `--interactive` cannot be used together.

**Independent Test**: `twmcp compile copilot-cli --select github --interactive` → exit 1.

### Tests

- [x] T018 [US4] Write test `test_select_and_interactive_exits_1` in tests/test_cli.py (TestCompileSelectInteractiveMutualExclusivity class) — both flags → exit 1, message mentions "mutually exclusive"

### Implementation

- [x] T019 [US4] Add mutual exclusivity check at top of `_resolve_selection()` in src/twmcp/cli.py: if `select is not None and interactive`, error + exit 1

**Checkpoint**: T018 must FAIL before T019. After T019, mutual exclusivity enforced.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup.

- [x] T020 Run full test suite via `make test`, verify all tests pass and coverage >= 85%
- [x] T021 Run quickstart.md validation commands from specs/005-simplify-select/quickstart.md
- [x] T022 Verify no monkey-patch references remain: `grep -r "_flag_needs_value\|_apply_select_patch\|_install_select_patch\|_INTERACTIVE" src/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US1+US2)**: Depends on Phase 1 (selector.py must handle `none` before CLI can use it)
- **Phase 3 (US3+US5)**: Depends on Phase 1 only (independent of Phase 2)
- **Phase 4 (US4)**: Depends on Phase 3 (--interactive must exist before checking mutual exclusivity)
- **Phase 5 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Already implemented — regression check only (Phase 2)
- **US2 (P1)**: Depends on Phase 1 foundational selector.py changes
- **US3 (P2)**: Independent of US1/US2 — depends only on Phase 1
- **US4 (P2)**: Depends on US3 (--interactive must exist)
- **US5 (P1)**: Coupled with US3 — implemented together in Phase 3

### Parallel Opportunities

- T001-T004: All selector tests can run in parallel (different test methods, same file)
- T006-T009: All US2 CLI tests can run in parallel
- Phase 2 and Phase 3 can proceed in parallel after Phase 1 completes

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Implementation tasks within a phase are sequential (same files)

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: selector.py `none` keyword
2. Complete Phase 2: US1+US2 non-interactive --select
3. **STOP and VALIDATE**: `twmcp compile copilot-cli --select none --dry-run` works
4. This is a useful increment even without --interactive

### Full Delivery

1. Phase 1 → Phase 2 + Phase 3 (parallel) → Phase 4 → Phase 5
2. Each phase adds value without breaking previous phases

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 22 |
| US1 tasks | 1 (regression check) |
| US2 tasks | 5 (tests) + 1 (impl) |
| US3 tasks | 3 (test updates) + 2 (impl) |
| US4 tasks | 1 (test) + 1 (impl) |
| US5 tasks | 1 (removal) |
| Foundational | 5 (selector.py) |
| Polish | 3 |
| Parallel opportunities | T001-T004, T006-T009, Phase 2 ∥ Phase 3 |
| MVP scope | Phase 1 + Phase 2 (US1+US2 only) |

## Verification

After implementation, run:
```bash
make test                    # All tests pass, coverage >= 85%
grep -r "_flag_needs_value\|_apply_select_patch\|_install_select_patch" src/  # No results
uv run twmcp compile copilot-cli --select none --dry-run --config tests/fixtures/sample_config.toml  # Empty config
```
