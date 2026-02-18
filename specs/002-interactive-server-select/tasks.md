# Tasks: Interactive MCP Server Selection

**Input**: Design documents from `/specs/002-interactive-server-select/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-contract.md

**Tests**: Included — TDD is mandatory per constitution (write tests FIRST, verify FAIL, then implement).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project (src/ layout)**: `src/twmcp/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependency required by all user stories

- [x] T001 Add `simple-term-menu` to `[project] dependencies` in pyproject.toml and run `uv sync` to install

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Selector utility functions and Click dual-mode patch — MUST complete before any user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Write failing tests for `parse_select_value()` and `validate_server_names()` in tests/test_selector.py — cover: comma splitting, whitespace stripping, empty string error, valid names pass-through, unknown names raise ValueError with available list
- [x] T003 Implement `parse_select_value()`, `validate_server_names()`, and `is_interactive_terminal()` in src/twmcp/selector.py — make T002 tests pass
- [x] T004 Add `--select` `Optional[str]` parameter to `compile` command, define `_INTERACTIVE` sentinel, and implement `_patch_select_option()` Click patch in src/twmcp/cli.py — per research.md Decision 1

**Checkpoint**: Foundation ready — `selector.py` utilities work, `--select` accepts bare flag and value. User story implementation can begin.

---

## Phase 3: User Story 1 — Interactive Server Selection (Priority: P1) MVP

**Goal**: User runs `twmcp compile copilot-cli --select` and gets an interactive multi-select prompt showing all servers with name and type. Only selected servers appear in compiled output.

**Independent Test**: `twmcp compile copilot-cli --select --dry-run` with mocked TerminalMenu — verify prompt is called with correct choices and output contains only selected servers.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T005 [P] [US1] Write failing tests for `select_servers_interactive()` in tests/test_selector.py — mock `TerminalMenu` to cover: all selected returns all names, subset returns subset, cancel (None) returns None, empty tuple returns empty list, verify labels show `name [type]` format
- [x] T006 [P] [US1] Write failing CLI tests for `--select` bare interactive mode in tests/test_cli.py — mock `select_servers_interactive` in `twmcp.selector` to cover: selected servers appear in output, cancelled exits with code 0, empty selection prints message and exits 0, non-TTY exits with code 1 and error message

### Implementation for User Story 1

- [x] T007 [US1] Implement `select_servers_interactive()` in src/twmcp/selector.py — use `TerminalMenu` with `multi_select=True`, `preselected_entries` for all items, labels as `name [type]`, return selected names or None on cancel
- [x] T008 [US1] Wire interactive selection flow into `compile()` in src/twmcp/cli.py — when `select == _INTERACTIVE`: check TTY via `is_interactive_terminal()`, call `select_servers_interactive()`, handle cancel (exit 0), handle empty (print message, exit 0), filter `canonical.servers` by selected names, pass filtered `CanonicalConfig` to `_compile_single`

**Checkpoint**: User Story 1 fully functional. `twmcp compile copilot-cli --select` works interactively with single-agent compilation.

---

## Phase 4: User Story 2 — Non-Interactive Filtering (Priority: P2)

**Goal**: User runs `twmcp compile copilot-cli --select github,local-proxy` and only those servers are compiled. No interactive prompt. Invalid names produce clear error.

**Independent Test**: `twmcp compile copilot-cli --select github,local-proxy --dry-run` — verify output contains exactly those servers. `--select unknown-server` exits with code 1 and lists available servers.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [US2] Write failing CLI tests for `--select <value>` filter mode in tests/test_cli.py — cover: valid names produce filtered output, unknown name exits 1 with error listing available servers, mixed valid+invalid names exits 1, comma-separated parsing works

### Implementation for User Story 2

- [x] T010 [US2] Implement non-interactive filter flow in `compile()` in src/twmcp/cli.py — when `select` is a string (not `_INTERACTIVE`): call `parse_select_value()`, call `validate_server_names()` (catch ValueError, print error + available, exit 1), filter `canonical.servers`, pass filtered `CanonicalConfig` to `_compile_single`

**Checkpoint**: User Story 2 fully functional. Non-interactive `--select github,local-proxy` works for single-agent compilation.

---

## Phase 5: User Story 3 — --all + --select (Priority: P3)

**Goal**: User runs `twmcp compile --all --select` and the selection (interactive or value) is applied once, then used for all agents.

**Independent Test**: `twmcp compile --all --select --dry-run` — verify prompt appears once, all agent outputs contain only selected servers (subject to agent compatibility).

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [US3] Write failing CLI tests for `--all --select` and `--all --select <value>` combinations in tests/test_cli.py — cover: interactive prompt called once for --all --select (mock), --all --select <value> filters all agents, incompatible servers still skipped per agent rules

### Implementation for User Story 3

- [x] T012 [US3] Refactor selection flow in src/twmcp/cli.py to extract `_resolve_selection()` helper that returns filtered `CanonicalConfig` — call it once in `compile()` before branching to `_compile_single`/`_compile_all`, pass filtered config to both paths

**Checkpoint**: All three active user stories functional. Selection works with both single agent and --all.

---

## Phase 6: User Story 4 — Backward Compatibility (Priority: P4)

**Goal**: Existing `compile` invocations without `--select` produce identical output.

**Independent Test**: Run all existing tests in tests/test_cli.py — they must pass unchanged.

- [x] T013 [US4] Run full existing test suite via `uv run python -m pytest tests/ -v` and verify all pre-existing tests pass unchanged — no regressions in tests/test_cli.py `TestCompileCommand`, `TestCompileAll`, `TestAgentsCommand`, `TestCompileWithInterpolation`

**Checkpoint**: All user stories complete. Backward compatibility verified.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, coverage, and final validation

- [x] T014 [P] Add edge case tests in tests/test_cli.py and tests/test_selector.py — cover: non-TTY with bare --select, empty string --select value, single-server config, `--select` with `=` syntax (`--select=github`), all selected servers incompatible with agent
- [x] T015 Run full test suite with coverage via `uv run python -m pytest tests/ --cov=twmcp` and verify ≥85% coverage per constitution

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──→ Phase 2: Foundational ──→ Phase 3-6: User Stories ──→ Phase 7: Polish
                           │
                           ├──→ Phase 3: US1 (P1) MVP
                           ├──→ Phase 4: US2 (P2) — can start after Phase 2
                           ├──→ Phase 5: US3 (P3) — depends on US1+US2 wiring
                           └──→ Phase 6: US4 (P4) — runs after all changes
```

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. Can start immediately after foundation.
- **US2 (P2)**: Depends on Phase 2 only. Can run in parallel with US1 (different code paths in cli.py).
- **US3 (P3)**: Depends on US1 and US2 being wired — selection flow must exist before refactoring for --all.
- **US4 (P4)**: Depends on all stories being complete — runs existing tests as final regression check.

### Within Each User Story (TDD Cycle)

1. Write failing tests (Red)
2. Implement to pass tests (Green)
3. Refactor if needed (Refactor)

### Parallel Opportunities

- **Phase 3**: T005 and T006 can run in parallel (tests in different files)
- **Phase 3-4**: US1 and US2 can proceed concurrently after Phase 2
- **Phase 7**: T014 edge case tests across files can run in parallel

---

## Parallel Example: User Story 1

```
# Launch test writing in parallel (different files):
T005: Write select_servers_interactive tests in tests/test_selector.py
T006: Write CLI interactive mode tests in tests/test_cli.py

# Then implement sequentially:
T007: Implement select_servers_interactive (makes T005 pass)
T008: Wire CLI flow (makes T006 pass)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T004)
3. Complete Phase 3: User Story 1 (T005-T008)
4. **STOP and VALIDATE**: `twmcp compile copilot-cli --select --dry-run` works interactively
5. Existing tests still pass (quick regression)

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add US1 (interactive) → **MVP — core feature works**
3. Add US2 (non-interactive) → scripting support
4. Add US3 (--all) → full flag coverage
5. Run US4 regression + Polish → ship-ready

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- TDD is mandatory: write tests first, verify they fail, then implement
- `simple-term-menu` `TerminalMenu` must be mocked in tests (no real TTY in test runner)
- Click `_flag_needs_value` patch is documented workaround — see research.md Decision 1
- Server filtering uses dict comprehension on `canonical.servers` — no new abstractions
