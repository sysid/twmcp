# Tasks: MCP Config Compiler

**Input**: Design documents from `/specs/001-mcp-config-compiler/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-contract.md

**Tests**: Included — constitution mandates TDD (Test-First NON-NEGOTIABLE).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization and test infrastructure

- [X] T001 Create project directory structure: `twmcp/`, `tests/`, `tests/fixtures/`, `tests/fixtures/expected/` per plan.md
- [X] T002 Configure pyproject.toml: add typer dependency, pytest/ruff/coverage config per constitution, entry point `twmcp = "twmcp.cli:app"`
- [X] T003 [P] Create test fixtures in tests/fixtures/sample_config.toml (canonical config with 3 servers: stdio, http, sse; includes overrides and variable placeholders) and tests/fixtures/sample_secrets.env (dotenv with test values)
- [X] T004 [P] Create shared test fixtures in tests/conftest.py (tmp_path helpers, config loading, env var patching)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and registries that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Tests

- [X] T005 [P] Write tests for AgentProfile dataclass and registry in tests/test_agents.py: test profile lookup by name, test all 3 built-in profiles (copilot-cli, intellij, claude-desktop), test unknown agent error, test profile fields match data-model.md
- [X] T006 [P] Write tests for canonical config loading in tests/test_config.py: test TOML parsing into CanonicalConfig model, test server field extraction, test override parsing, test validation (missing required fields, invalid type), test empty/missing config error

### Implementation

- [X] T007 [P] Implement AgentProfile dataclass and AGENT_REGISTRY in twmcp/agents.py: 3 built-in profiles per data-model.md agent profile registry table (copilot-cli, intellij, claude-desktop), get_profile(name) function
- [X] T008 [P] Implement CanonicalConfig, Server, PartialServer dataclasses and load_config(path) in twmcp/config.py: TOML parsing via tomllib, validation per data-model.md validation rules, no interpolation yet (wired in Phase 4)

**Checkpoint**: Config loading + agent registry work independently. `pytest tests/test_agents.py tests/test_config.py` passes.

---

## Phase 3: User Story 1 - Compile single agent (Priority: P1) MVP

**Goal**: User runs `twmcp compile copilot-cli` and gets a valid agent-specific JSON file

**Independent Test**: Load sample_config.toml (with literal values, no variables), compile for copilot-cli, verify output matches tests/fixtures/expected/copilot-cli.json

### Tests

- [X] T009 [P] [US1] Write tests for compiler transformation in tests/test_compiler.py: test transform_for_agent() produces correct JSON structure per agent (top_level_key, type_mapping, header_style), test override merging, test unsupported field skipping with stderr warning, test JSON file writing to tmp_path, test dry-run returns dict without writing
- [X] T010 [P] [US1] Write tests for CLI compile command in tests/test_cli.py: test `twmcp compile copilot-cli` end-to-end with sample config, test `--dry-run` prints to stdout, test unknown agent error message and exit code 1, test `--config` flag overrides default path

### Implementation

- [X] T011 [US1] Implement transform_for_agent(config, profile) and write_config(compiled, path) in twmcp/compiler.py: apply type_mapping, header_style conversion, override merging per data-model.md, skip unsupported fields with stderr warning, write JSON with indent=2
- [X] T012 [US1] Implement typer app with `compile` command in twmcp/cli.py: agent argument, --config option (default ~/.config/twmcp/config.toml), --dry-run flag, error handling per cli-contract.md error format
- [X] T013 [US1] Create expected output fixtures in tests/fixtures/expected/copilot-cli.json, tests/fixtures/expected/intellij.json, tests/fixtures/expected/claude-desktop.json and wire entry point in twmcp/__init__.py

**Checkpoint**: `twmcp compile copilot-cli --dry-run --config tests/fixtures/sample_config.toml` produces valid JSON. `pytest tests/` passes.

---

## Phase 4: User Story 4 - Variable interpolation (Priority: P2)

**Goal**: `${VAR}` and `${VAR:-default}` placeholders in canonical config resolve to concrete values from env vars and dotenv files

**Independent Test**: Load sample_config.toml with `${GITHUB_TOKEN}` placeholder, set env var, compile, verify output contains actual value

### Tests

- [X] T014 [P] [US4] Write tests for variable resolver in tests/test_interpolate.py: test resolve `${VAR}` from env, test `${VAR:-default}` when VAR not set, test `${VAR:-default}` when VAR is set (env wins), test multiple variables in one string, test dotenv file loading, test env var precedence over dotenv, test unresolved variable raises error listing ALL missing vars, test missing dotenv file error
- [X] T015 [P] [US4] Write CLI integration test with variables in tests/test_cli.py: test compile with env vars set produces resolved output, test compile with unresolved var fails with clear error listing all missing vars

### Implementation

- [X] T016 [US4] Implement resolve_variables(text, variables) and load_dotenv(path) in twmcp/interpolate.py: regex pattern for `${VAR_NAME}` and `${VAR_NAME:-default}`, collect all unresolved vars before failing, dotenv parser (KEY=VALUE lines, skip comments/blanks)
- [X] T017 [US4] Wire interpolation into config loading: call interpolate on all string values in CanonicalConfig after TOML parse in twmcp/config.py, build variable map from env + optional dotenv (env takes precedence)

**Checkpoint**: `twmcp compile copilot-cli --dry-run` with `${GITHUB_TOKEN}` set resolves correctly. Unset vars produce clear error. `pytest tests/` passes.

---

## Phase 5: User Story 2 - Compile all agents (Priority: P2)

**Goal**: `twmcp compile --all` regenerates configs for every registered agent

**Independent Test**: Run `--all` with sample config, verify all 3 agent output files exist with correct structure

### Tests

- [X] T018 [US2] Write tests for --all flag in tests/test_cli.py: test `--all` compiles for all 3 agents, test `--all --dry-run` prints all configs separated by agent headers, test `--all` with one agent failing still reports all errors

### Implementation

- [X] T019 [US2] Add --all flag to compile command in twmcp/cli.py: iterate AGENT_REGISTRY, compile each, report per-agent success/failure to stderr

**Checkpoint**: `twmcp compile --all --dry-run` outputs configs for all 3 agents. `pytest tests/` passes.

---

## Phase 6: User Story 3 - List agents (Priority: P3)

**Goal**: `twmcp agents` shows a table of supported agents with config paths

**Independent Test**: Run `twmcp agents` and verify output contains all 3 agent names, paths, and keys

### Tests

- [X] T020 [US3] Write tests for agents command in tests/test_cli.py: test table output contains all 3 agents with correct paths, test `--json` outputs valid JSON array with name/config_path/top_level_key fields

### Implementation

- [X] T021 [US3] Implement `agents` command in twmcp/cli.py: Rich table for default output (columns: Agent, Config Path, Key), JSON array for --json flag

**Checkpoint**: `twmcp agents` and `twmcp agents --json` both work. `pytest tests/` passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, coverage, validation

- [X] T022 [P] Add edge case tests in tests/test_config.py: empty config file, malformed TOML, missing servers section, config file not found
- [X] T023 [P] Add edge case tests in tests/test_compiler.py: server with all optional fields empty, override for unknown agent (warn), create intermediate directories for output
- [X] T024 Verify 85% coverage threshold: run `pytest --cov=twmcp --cov-report=term --cov-fail-under=85` and fix gaps
- [X] T025 Run quickstart.md validation: follow specs/001-mcp-config-compiler/quickstart.md steps end-to-end and verify all commands work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — MVP
- **US4 (Phase 4)**: Depends on US1 (adds interpolation to existing compile flow)
- **US2 (Phase 5)**: Depends on US1 (extends compile with --all)
- **US3 (Phase 6)**: Depends on Foundational only (independent of compile)
- **Polish (Phase 7)**: Depends on all stories complete

### User Story Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ├──────────────────────┐
    ▼                      ▼
Phase 3 (US1 - MVP)    Phase 6 (US3 - list agents)
    │
    ├──────────┐
    ▼          ▼
Phase 4     Phase 5
(US4)       (US2)
    │          │
    └────┬─────┘
         ▼
    Phase 7 (Polish)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/dataclasses before services/logic
- Core logic before CLI wiring
- Commit after each task or logical group

### Parallel Opportunities

**Phase 1**: T003 and T004 can run in parallel
**Phase 2**: T005 ∥ T006 (tests), T007 ∥ T008 (implementation)
**Phase 3**: T009 ∥ T010 (tests)
**Phase 4**: T014 ∥ T015 (tests)
**Phase 6**: Can run in parallel with Phase 4 or 5 (independent)
**Phase 7**: T022 ∥ T023

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 — single agent compile
4. **STOP and VALIDATE**: `twmcp compile copilot-cli --dry-run` works
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → compile single agent with literal values (MVP!)
3. US4 → add variable interpolation (real-world ready)
4. US2 → compile all agents at once (convenience)
5. US3 → list agents (discovery)
6. Polish → edge cases, coverage, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Constitution: TDD mandatory — tests first, verify they fail, then implement
- Constitution: 85% coverage minimum
- Single external dependency: typer (justified by CLI framework + Rich tables)
- All other deps are stdlib (tomllib, re, json, pathlib)
