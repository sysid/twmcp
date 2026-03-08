# Tasks: Project-Local Agent Configurations

**Input**: Design documents from `/specs/006-local-agent-configs/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: Included — constitution mandates TDD (Test-First, NON-NEGOTIABLE).

**Organization**: Tasks grouped by user story. US1 and US2 are both P1 but independent. US3 depends on US1 completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - Compile Claude Code MCP Config (Priority: P1) 🎯 MVP

**Goal**: Add `claude-code` agent profile that writes to `.claude/mcp-config.json` with `mcpServers` key, `type` field, flat headers, all server types supported.

**Independent Test**: `uv run twmcp compile claude-code --dry-run --config tests/fixtures/sample_config.toml` produces correct JSON.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T001 [P] [US1] Add `test_claude_code_profile` test in tests/test_agents.py: verify name, config_path=`.claude/mcp-config.json`, top_level_key=`mcpServers`, type_mapping=`{}`, header_style=`flat`
- [x] T002 [P] [US1] Add `test_claude_code_includes_all_servers` test in tests/test_compiler.py: verify stdio, http, and sse servers are all included (not skipped)
- [x] T003 [P] [US1] Add `test_claude_code_includes_type_field` test in tests/test_compiler.py: verify `type` field is present in output (unlike claude-desktop)
- [x] T004 [P] [US1] Add `test_claude_code_flat_headers` test in tests/test_compiler.py: verify headers appear as flat `headers` key (not nested in `requestInit`)
- [x] T005 [P] [US1] Update `test_list_agents_returns_all` in tests/test_agents.py: add `claude-code` to expected set
- [x] T006 [P] [US1] Update `test_registry_has_three_agents` in tests/test_agents.py: change count from 3 to 4

### Implementation for User Story 1

- [x] T007 [US1] Add `claude-code` AgentProfile entry to `AGENT_REGISTRY` in src/twmcp/agents.py with config_path=`Path(".claude") / "mcp-config.json"`, top_level_key=`mcpServers`, type_mapping=`{}`, header_style=`flat`

**Checkpoint**: All T001-T006 tests pass. `twmcp compile claude-code --dry-run` produces correct JSON with type field, flat headers, and all server types.

---

## Phase 2: User Story 2 - Copilot CLI Project-Local Config (Priority: P1)

**Goal**: Change copilot-cli config path from global `~/.copilot/mcp-config.json` to project-local `.copilot/mcp-config.json`. JSON format unchanged.

**Independent Test**: `uv run twmcp compile copilot-cli --dry-run --config tests/fixtures/sample_config.toml` works; `twmcp agents` shows `.copilot/mcp-config.json` (not `~/.copilot/...`).

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T008 [US2] Update `test_copilot_cli_profile` in tests/test_agents.py: assert config_path equals `Path(".copilot") / "mcp-config.json"` (relative, not global)

### Implementation for User Story 2

- [x] T009 [US2] Change copilot-cli `config_path` in src/twmcp/agents.py from `Path.home() / ".copilot" / "mcp-config.json"` to `Path(".copilot") / "mcp-config.json"`

**Checkpoint**: T008 test passes. copilot-cli JSON format unchanged, only path is different. All existing copilot-cli compiler tests still pass.

---

## Phase 3: User Story 3 - Compile All Includes Claude-Code (Priority: P2)

**Goal**: `twmcp compile --all` includes claude-code alongside existing agents.

**Independent Test**: `uv run twmcp compile --all --dry-run --config tests/fixtures/sample_config.toml` shows claude-code section.

No additional tasks needed — US3 is satisfied automatically once US1 adds claude-code to the registry. The `--all` flag iterates `AGENT_REGISTRY`, which already includes the new entry after T007.

**Checkpoint**: `twmcp compile --all --dry-run` output includes `--- claude-code ---` section.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation

- [x] T010 Update CLAUDE.md Recent Changes section with `006-local-agent-configs` entry
- [x] T011 Update README.md agent list/documentation to include claude-code and reflect copilot-cli path change
- [x] T012 Run full test suite: `uv run python -m pytest tests/ -v --cov=twmcp --cov-report=term-missing`
- [x] T013 Run quickstart.md verification commands

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)** and **Phase 2 (US2)**: Independent — can run in parallel (different profile entries, tests in different test classes)
- **Phase 3 (US3)**: Satisfied automatically by US1 completion (no additional tasks)
- **Phase 4 (Polish)**: Depends on US1 + US2 completion

### Within Each User Story

- Tests (T001-T006, T008) MUST be written and FAIL before implementation (T007, T009)
- Each story modifies the same file (agents.py) but different entries — no conflict

### Parallel Opportunities

- T001-T006 can all run in parallel (different test methods, same file but no conflicts)
- US1 and US2 can be implemented in parallel (different registry entries)

---

## Parallel Example: User Story 1

```bash
# Write all US1 tests in parallel:
Task: "T001 - claude-code profile test in tests/test_agents.py"
Task: "T002 - claude-code includes all servers in tests/test_compiler.py"
Task: "T003 - claude-code type field test in tests/test_compiler.py"
Task: "T004 - claude-code flat headers test in tests/test_compiler.py"
Task: "T005 - update agent list test in tests/test_agents.py"
Task: "T006 - update agent count test in tests/test_agents.py"

# Then implement:
Task: "T007 - add claude-code to AGENT_REGISTRY in src/twmcp/agents.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Write T001-T006 tests → verify they FAIL
2. Implement T007 → verify tests PASS
3. **STOP and VALIDATE**: `twmcp compile claude-code --dry-run` works

### Incremental Delivery

1. US1 (claude-code profile) → Test → Validate
2. US2 (copilot-cli path change) → Test → Validate
3. Polish (docs, full test suite) → Done

---

## Notes

- Total tasks: 13
- US1: 7 tasks (6 test + 1 implementation)
- US2: 2 tasks (1 test + 1 implementation)
- US3: 0 tasks (satisfied by US1)
- Polish: 4 tasks
- Both US1 and US2 modify `src/twmcp/agents.py` but different entries — no merge conflict
- No new files created, no new dependencies
