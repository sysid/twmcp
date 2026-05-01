# Tasks: Named Server Profiles

**Input**: Design documents from `/specs/008-server-profiles/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-behavior.md, quickstart.md
**Tests**: TDD is mandatory per the project constitution — failing tests are written first for every functional task.

**Organization**: Tasks are grouped by user story (P1 → P2 → P3) so each
story is independently implementable, testable, and shippable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependencies on incomplete tasks)
- **[Story]**: User story tag — `[US1]`, `[US2]`, `[US3]`
- All paths absolute or rooted at the repo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: One-time scaffolding for the feature.

- [X] T001 [P] Create test fixture `tests/fixtures/sample_config_with_profiles.toml` containing 3 servers (e.g. `server-a`, `server-b`, `server-c`) and 2 profiles (`emea = ["server-a", "server-b"]`, `apac = ["server-c"]`, plus an `empty = []` profile for edge-case tests)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema and parser changes that every user story depends on.

**⚠️ CRITICAL**: No user-story phase may begin until this phase is green.

- [X] T002 Write failing tests in `tests/test_config.py` for `_parse_profiles`: (a) missing `[profiles]` → empty dict on `CanonicalConfig.profiles`; (b) valid `[profiles]` → expected dict; (c) `[profiles]` not a table → `ValueError`; (d) profile value not a list → `ValueError`; (e) list entry not a string → `ValueError`; (f) empty list `[]` → empty list (valid)
- [X] T003 Add `profiles: dict[str, list[str]] = field(default_factory=dict)` to `CanonicalConfig` in `src/twmcp/config.py`
- [X] T004 Implement `_parse_profiles(raw: dict) -> dict[str, list[str]]` in `src/twmcp/config.py` next to `_parse_agent_overrides`; wire it into `_parse_raw` so `CanonicalConfig.profiles` is populated; structural validation only (no server-reference check at load time, per research.md Decision 5)
- [X] T005 Add debug logging in `_parse_profiles`: one line per parsed profile (name + count), one line when no `[profiles]` section is present — mirrors the existing `_parse_agent_overrides` logging style
- [X] T006 Verify all tests from T002 pass; run full suite to confirm zero regressions on existing 242 tests

**Checkpoint**: Profile schema lives in `CanonicalConfig` and is fully parsed/validated. User stories may now begin.

---

## Phase 3: User Story 1 — Compile a Predefined Profile (Priority: P1) 🎯 MVP

**Goal**: User can run `twmcp compile <agent> --profile emea` and have the compiled output contain only the profile's servers. Without `--profile`, behavior is unchanged.

**Independent Test**: Run `twmcp compile copilot-cli --profile emea --dry-run --config tests/fixtures/sample_config_with_profiles.toml` and assert the output contains exactly `server-a` and `server-b` under `mcpServers`. Run without `--profile` and assert all 3 servers are present.

### Tests for User Story 1 (write first; verify red)

- [X] T007 [P] [US1] Add tests in `tests/test_selector.py` (create file if absent) for `_resolve_profile`: (a) unknown profile name with no profiles defined → `ValueError` with "No profiles defined"; (b) unknown profile with available list → `ValueError` listing available names sorted; (c) profile references missing server(s) → `ValueError` listing each missing name; (d) valid profile → returns the set of expected server names; (e) empty profile `[]` → returns empty set; (f) profile with duplicates → deduplicated result
- [X] T008 [P] [US1] Add CLI integration tests in `tests/test_cli.py` for `compile --profile`: (a) valid profile filters output; (b) `--profile` + `--select` exits 1 with mutual-exclusion error to stderr; (c) unknown profile exits 1 with "Unknown profile" message listing available names; (d) profile referencing missing server exits 1 naming the missing server; (e) `compile --all --profile emea` filters every agent's output uniformly; (f) `compile <agent>` (no `--profile`) is unchanged from current behavior

### Implementation for User Story 1

- [X] T009 [US1] Implement `_resolve_profile(name: str, canonical: CanonicalConfig) -> set[str]` in `src/twmcp/selector.py`: validate profile name against `canonical.profiles` keys (raise with sorted available list, or "No profiles defined" message when empty); validate each server name against `canonical.servers` keys (raise listing all missing); return a set of valid server names
- [X] T010 [US1] Add `--profile <name>` option to the `compile` command in `src/twmcp/cli.py`
- [X] T011 [US1] Extend `_resolve_selection` in `src/twmcp/cli.py` to handle `--profile`: (a) error on `--profile` + `--select` (mutual exclusion, exit 1); (b) when `--profile` alone, resolve via `_resolve_profile`, build filtered `CanonicalConfig`, return; (c) preserve existing branches and the no-flag default; convert `_resolve_profile`'s `ValueError` into a typer.echo + Exit(1) at this layer
- [X] T012 [US1] Add debug logging at the profile-resolution decision point in `cli._resolve_selection` per FR-010 and contracts/cli-behavior.md: log requested profile, resolved server count + sorted list, and excluded server count + sorted list
- [X] T013 [US1] Verify all tests from T007 and T008 pass; run full suite to confirm zero regressions

**Checkpoint**: `--profile` works end-to-end. Feature is shippable as MVP.

---

## Phase 4: User Story 2 — Discover Available Profiles (Priority: P2)

**Goal**: User can run `twmcp profiles` to see all defined profiles and their member servers without opening the TOML file.

**Independent Test**: Run `twmcp profiles --config tests/fixtures/sample_config_with_profiles.toml` and assert `emea` and `apac` appear with their server lists. Run with `--json` and assert valid JSON array. Run against a config with no `[profiles]` section and assert exit 0 with a "no profiles defined" message.

### Tests for User Story 2 (write first; verify red)

- [X] T014 [P] [US2] Add CLI integration tests in `tests/test_cli.py` for the `profiles` command: (a) table output lists each profile name with its servers; (b) `--json` produces a JSON array of `{"name": ..., "servers": [...]}` objects sorted by name; (c) config with no `[profiles]` table → exit 0 with stderr message "No profiles defined in <config>"; (d) `profiles --json` against profile-less config → empty `[]` to stdout; (e) `--config` flag respected; (f) missing config file → same warning behavior as the existing `agents` command (does not crash)

### Implementation for User Story 2

- [X] T015 [US2] Add `profiles` command to `src/twmcp/cli.py`, mirroring the structure of the existing `agents` command — accept `--json` and `--config` flags, share the same config-load error handling
- [X] T016 [US2] Implement table-mode output: header row, one line per profile sorted by name, server names comma-joined; mirror column widths used by `agents`
- [X] T017 [US2] Implement `--json` output: list of `{"name": str, "servers": list[str]}` objects sorted by profile name
- [X] T018 [US2] Verify all tests from T014 pass; run full suite

**Checkpoint**: Discovery works. Story 2 is shippable.

---

## Phase 5: User Story 3 — Profile + Interactive Pre-seeding (Priority: P3)

**Goal**: User can run `twmcp compile <agent> --profile emea --interactive` and the picker opens with the profile's servers pre-selected.

**Independent Test**: Run `compile <agent> --profile emea --interactive` against the test fixture in a fake-tty session (or with `select_servers_interactive` mocked) and assert the menu's `preselected_entries` contain the profile's server names. Run `--profile emea --select x` and assert mutual-exclusion error.

### Tests for User Story 3 (write first; verify red)

- [X] T019 [P] [US3] Add tests in `tests/test_cli.py` for `compile --profile <name> --interactive`: (a) mock `select_servers_interactive` and assert it is called with a `preselected` argument containing the profile's server names; (b) `--profile` + `--select` together → exit 1 with mutual-exclusion error (already tested in T008 — extend to confirm precedence rules)
- [X] T020 [P] [US3] Add a unit test in `tests/test_selector.py` for `select_servers_interactive(servers, preselected=...)`: confirms the preselected set is forwarded to `TerminalMenu`'s `preselected_entries` parameter

### Implementation for User Story 3

- [X] T021 [US3] Extend `select_servers_interactive` in `src/twmcp/selector.py` to accept an optional `preselected: Iterable[str] | None = None` parameter and pass it through to `TerminalMenu(..., preselected_entries=...)` (verified available in the installed version)
- [X] T022 [US3] Update `_resolve_selection` in `src/twmcp/cli.py` so that when both `--profile` and `--interactive` are set, the profile's resolved server names are passed as `preselected` to `select_servers_interactive`; the user's confirmed selection (which may be a subset) becomes the filter
- [X] T023 [US3] Verify all tests from T019 and T020 pass; run full suite

**Checkpoint**: Pre-seeded interactive selection works. Story 3 is shippable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, edge cases, and final cleanup. Per Constitution Principle IV, the task is not complete until docs reflect the changes.

- [X] T024 [P] Update `README.md`: add a "Profiles" subsection under CLI Reference covering `[profiles]` schema, `--profile <name>` flag, `twmcp profiles` command, and the precedence/mutual-exclusion rules from `contracts/cli-behavior.md`
- [X] T025 [P] Update `CLAUDE.md` (project root) "Active Technologies" and "Recent Changes" sections to mention `[profiles]` support added in 008-server-profiles (the agent-context script seeded the entry — verify wording is accurate and trim any duplication)
- [X] T026 [P] Update `src/twmcp/editor.py` `init_config` template to include a commented-out `[profiles]` example block, consistent with how `[agents.*]` overrides are seeded today
- [X] T027 Verify the quickstart in `specs/008-server-profiles/quickstart.md` runs end-to-end against `tests/fixtures/sample_config_with_profiles.toml` — every command shown should produce the documented output (manual smoke test, results captured in commit message)
- [X] T028 Run full test suite (`make test`), confirm zero regressions, confirm coverage on new code paths is meaningful (new modules in `selector.py` and the `profiles` command should not have uncovered branches)

---

## Dependency Graph

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ──────────────────────────┐
    │                                            │
    ▼                                            ▼
Phase 3 (US1 — MVP)         Phase 4 (US2)    [US2 depends only on Phase 2]
    │                            │
    ▼                            │
Phase 5 (US3)                    │            [US3 depends on US1's --profile flag plumbing]
    │                            │
    ▼                            ▼
                Phase 6 (Polish)
```

| Phase | Depends on | Can run in parallel with |
|---|---|---|
| Phase 1 | — | — |
| Phase 2 | Phase 1 | — |
| Phase 3 (US1) | Phase 2 | Phase 4 |
| Phase 4 (US2) | Phase 2 | Phase 3 |
| Phase 5 (US3) | Phase 3 (T011) | — |
| Phase 6 | Phases 3-5 | — |

## Parallel Execution Opportunities

Within Phase 2: T002 (test) must precede T003-T005, which are sequential
in the same file. T006 is a verification gate.

Within Phase 3: T007 and T008 can be authored in parallel (different
files); T009-T012 are sequential because they touch overlapping logic in
`cli.py` and `selector.py`. T013 is a gate.

Within Phase 6: T024, T025, T026 are all `[P]` — different files.

## Implementation Strategy

**MVP scope**: Phases 1, 2, 3 only. After Phase 3, the feature is
shippable: users get `[profiles]` support and `--profile <name>` on
`compile`. Phases 4 (discovery) and 5 (interactive pre-seed) are
incremental enhancements, each independently deliverable.

**Recommended ship order**: MVP → US2 (discoverability completes the UX
loop) → US3 (refinement, lowest demand). Phase 6 should land alongside
each phase's merge, not deferred to the end — Constitution Principle IV
ties documentation to implementation.

## Independent Test Criteria (per story)

| Story | Single-command verification |
|---|---|
| US1 | `twmcp compile copilot-cli --profile emea --dry-run --config <fixture>` shows only profile servers |
| US2 | `twmcp profiles --config <fixture>` lists `emea` and `apac` with their members |
| US3 | `twmcp compile <agent> --profile emea --interactive` opens the picker with profile servers pre-selected (TTY required, or test via mocked `select_servers_interactive`) |

## Format Validation

All tasks above conform to `- [ ] TID [P?] [Story?] Description with file path`. Story tags are present on every Phase 3-5 task and absent on Phases 1-2 and 6, as required.
