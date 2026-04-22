# Tasks: Configurable Agent Output Paths

**Feature**: `007-configurable-config-paths`
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

TDD is mandatory per the project constitution — test tasks precede implementation within each story.

## Phase 1: Setup

- [X] T001 Add test fixture `tests/fixtures/sample_config_with_overrides.toml` containing `[agents.claude-code]`, `[agents.claude-desktop]` override entries, `${VAR}` placeholder, `~` path, and one `[servers.*]` entry so downstream tests share one realistic input

## Phase 2: Foundational (blocking prerequisites)

- [X] T002 Extend `CanonicalConfig` in `src/twmcp/config.py` with `agent_overrides: dict[str, str] = field(default_factory=dict)` (dataclass-only change; no parsing yet) — lets every downstream test import the updated type without breaking
- [X] T003 [P] Add `resolve_profile(name: str, overrides: dict[str, str]) -> AgentProfile` helper in `src/twmcp/agents.py` that returns the registry entry unchanged when no override matches, and otherwise a new `AgentProfile` whose `config_path` is `Path(overrides[name]).expanduser()`; raises via existing `get_profile` for unknown names

## Phase 3: User Story 1 — Override an agent's output path (P1)

**Story goal**: User can set `[agents.<name>] config_path = "..."` in `config.toml`; `twmcp compile <agent>` writes to that path instead of the built-in default. Variable / `~` expansion works. Invalid entries fail fast.

**Independent test**: Run `twmcp compile claude-code --config tests/fixtures/sample_config_with_overrides.toml` and assert the output file lands at the override path, not at `.claude/mcp-config.json`.

### Tests (write first, verify they FAIL)

- [X] T004 [P] [US1] Add failing test in `tests/test_config.py`: `load_and_resolve()` on the fixture parses `agent_overrides` as a `dict[str, str]` with the expected keys/values (unexpanded `${VAR}` gets resolved, unexpanded `~` left to caller)
- [X] T005 [P] [US1] Add failing test in `tests/test_config.py`: unknown agent name in `[agents.<name>]` raises `ValueError` whose message contains the offending name and the sorted list of valid agents
- [X] T006 [P] [US1] Add failing test in `tests/test_config.py`: non-string `config_path` (e.g. a TOML table or integer) raises `ValueError` naming the offending key and actual type
- [X] T007 [P] [US1] Add failing test in `tests/test_config.py`: missing `[agents]` section yields `agent_overrides == {}` (backwards-compat)
- [X] T008 [P] [US1] Add failing test in `tests/test_config.py`: empty `[agents.<name>]` (no `config_path` key) is silently accepted — `agent_overrides` simply lacks that key
- [X] T009 [P] [US1] Add failing test in `tests/test_agents.py`: `resolve_profile("claude-code", {"claude-code": "~/foo.json"})` returns a profile whose `config_path == Path.home() / "foo.json"`; with empty overrides returns the registry entry unchanged; unknown name raises `KeyError`
- [X] T010 [P] [US1] Add failing test in `tests/test_cli.py`: invoking `twmcp compile claude-code --config <fixture>` writes the compiled JSON at the fixture's override path (use `tmp_path` + `${PROJECT_ROOT}` env var to redirect) and does NOT create `.claude/mcp-config.json`
- [X] T011 [P] [US1] Add failing test in `tests/test_cli.py`: `twmcp compile --all --config <fixture>` writes each agent to its effective path (override where present, default where absent)
- [X] T012 [P] [US1] Add failing test in `tests/test_cli.py`: unknown agent in config produces exit code 1 and an error message mentioning the invalid name

### Implementation (make the tests pass)

- [X] T013 [US1] Implement `[agents.*]` parsing and validation in `src/twmcp/config.py` (`_parse_raw` or new `_parse_agent_overrides`): validate keys against `AGENT_REGISTRY`, validate each `config_path` is `str`, populate `CanonicalConfig.agent_overrides`; ensure the interpolation pre-scan / resolver walks `[agents.*]` values the same way it walks `[servers.*]`
- [X] T014 [US1] In `src/twmcp/cli.py`, thread `canonical.agent_overrides` into `_compile_single` and `_compile_all`: replace direct `get_profile(agent)` + `profile.config_path` usage with `resolve_profile(agent, canonical.agent_overrides)`; update the "Written:" stderr line to show the effective path
- [X] T015 [US1] Verify the existing `_load_config_or_exit` error path surfaces the new `ValueError` messages cleanly (no extra plumbing expected — confirm with an ad-hoc run using a broken fixture and adjust only if the message is swallowed)

**Checkpoint**: P1 MVP complete — overrides work end-to-end for `compile`. Story is independently shippable here.

## Phase 4: User Story 2 — Discover and edit defaults via `edit --init` (P2)

**Story goal**: `twmcp edit --init` on a clean system produces a `config.toml` containing a commented `[agents.<name>]` block for every registered agent, each seeded with its built-in default path, so users can uncomment and edit without reading docs.

**Independent test**: Run `twmcp edit --init --config <tmp>/config.toml` in a temp dir with no pre-existing file; parse the output; assert every registered agent appears as a commented block with the correct `config_path` string.

### Tests (write first, verify they FAIL)

- [X] T016 [P] [US2] Add failing test in `tests/test_editor.py` (new file): `init_config(tmp_path / "config.toml")` produces a file whose contents, when all `# [agents.<name>]` / `# config_path = "..."` lines are uncommented, parse as valid TOML matching the registry defaults
- [X] T017 [P] [US2] Add failing test in `tests/test_editor.py`: every agent in `AGENT_REGISTRY` appears exactly once in the seeded block (parametrized over registry entries — auto-covers future agents)
- [X] T018 [P] [US2] Add failing test in `tests/test_editor.py`: paths under the user's home directory are rendered as `~/...` (not absolute), matching the `twmcp agents` table convention

### Implementation

- [X] T019 [US2] Replace the static `DEFAULT_CONFIG_TEMPLATE` in `src/twmcp/editor.py` with a function (or template + runtime-appended block) that concatenates the existing header/servers example with a generated `# ---- Agent output paths (optional overrides) ----` section iterating `AGENT_REGISTRY` and formatting each path via `str(path).replace(str(Path.home()), "~")`
- [X] T020 [US2] Update `init_config(path)` to call the new generator so `twmcp edit --init` writes the full seeded template; keep the `FileExistsError` refusal unchanged

**Checkpoint**: P2 complete — new users discover overrides on first `--init`.

## Phase 5: User Story 3 — Verify effective paths via `twmcp agents` (P3)

**Story goal**: `twmcp agents` (text and `--json`) displays the effective `config_path` per agent (override if present, registry default otherwise), without a separate flag.

**Independent test**: With `sample_config_with_overrides.toml` selected via `--config`, running `twmcp agents` shows the override path for `claude-code`/`claude-desktop` and the default for `copilot-cli`/`intellij`; `--json` mirrors the same.

### Tests (write first, verify they FAIL)

- [X] T021 [P] [US3] Add failing test in `tests/test_cli.py`: `twmcp agents --config <fixture>` text output includes the override path string for agents with overrides and the registry default for others
- [X] T022 [P] [US3] Add failing test in `tests/test_cli.py`: `twmcp agents --json --config <fixture>` emits a JSON array whose `config_path` fields reflect effective paths
- [X] T023 [P] [US3] Add failing test in `tests/test_cli.py`: `twmcp agents` when `--config` points to a missing file prints a single `Warning:` line to stderr, exits 0, and still shows registry defaults (first-run discoverability)

### Implementation

- [X] T024 [US3] In `src/twmcp/cli.py`, add `config: Path = typer.Option(DEFAULT_CONFIG, ...)` to the `agents` command; attempt `load_and_resolve`, catch `FileNotFoundError` / `ValueError` → emit one-line stderr warning and continue with empty overrides
- [X] T025 [US3] Replace direct `list_agents()` iteration with `resolve_profile(a.name, overrides)` and display the resolved `config_path` (after applying the same `str(path).replace(str(Path.home()), "~")` shortening already used for defaults)

**Checkpoint**: P3 complete — effective paths are visible without invoking `compile --dry-run`.

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Update `README.md`: add `[agents.*]` to the TOML schema section; mention the new `--config` flag on `agents`; update the example `twmcp agents` output if one is embedded
- [X] T027 [P] Update `CLAUDE.md` "Recent Changes" entry for `007-configurable-config-paths` (prepend one-line summary; let update-agent-context.sh–added lines remain)
- [X] T028 Run `make format && make lint && make ty` and fix any findings
- [X] T029 Run `make test` and confirm ≥ 85% coverage (constitution requirement); if a new branch drops coverage, add a targeted test rather than lowering the threshold
- [X] T030 Manually walk through `quickstart.md` end-to-end against a fresh temp HOME to verify the documented flow works exactly as written; fix any drift

## Dependencies

```
Phase 1 (T001) ──┐
                 ├──> Phase 2 (T002, T003) ──┬──> Phase 3 US1 (T004–T015) ──┐
                 │                           │                              │
                 │                           ├──> Phase 4 US2 (T016–T020) ──┼──> Phase 6 Polish
                 │                           │                              │
                 │                           └──> Phase 5 US3 (T021–T025) ──┘
```

- T003 depends on T002 only because both live in code the tests will import; they can actually be done in parallel (marked [P]).
- US1, US2, US3 are independent after Phase 2 — any order or parallel; US1 is the MVP.
- Within each story phase, all `[P]` test tasks can run in parallel; implementation tasks in the same file are sequential.

## Parallel execution examples

**Kick off all US1 tests together** (different test functions, mostly different files):

```
T004, T005, T006, T007, T008 — tests/test_config.py (same file, sequential edits)
T009                          — tests/test_agents.py
T010, T011, T012              — tests/test_cli.py (same file, sequential edits)
```

Three developers/agents can own one test file each simultaneously.

**Polish phase**: T026 (README) and T027 (CLAUDE.md) are fully independent — run in parallel before T028/T029/T030 gates.

## Implementation strategy

- **MVP = Phase 1 + Phase 2 + Phase 3 (US1)**. At this point overrides are fully functional for `compile` / `compile --all`; ship immediately if a smaller scope is desired.
- **Incremental delivery**: US2 (init template) and US3 (agents display) are pure UX quality-of-life additions on top of a working MVP; they can ship in any order.
- **TDD enforcement**: every implementation task (T013–T015, T019–T020, T024–T025) must be preceded by red tests from the same story phase. Do not start an implementation task until the story's test tasks are written and failing.
