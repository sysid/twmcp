# Tasks: MCP Config to TOML Extractor

**Input**: Design documents from `/specs/003-mcp-to-toml/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contract.md

**Tests**: Included — constitution mandates TDD (Test-First, NON-NEGOTIABLE).

**Organization**: Tasks grouped by user story. US1 delivers a working MVP. US2 extends format coverage. US3 adds error handling.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create test fixtures needed across all user stories

- [x] T001 Create test fixture JSON files in tests/fixtures/: claude_desktop.json (mcpServers format with stdio server, env vars), vscode_mcp.json (mcp.servers format), flat_servers.json (servers format), with_secrets.json (literal secret values in env and headers), with_unknown_props.json (extra properties like "disabled": true)

---

## Phase 2: User Story 1 — Extract canonical TOML from MCP JSON (Priority: P1) 🎯 MVP

**Goal**: User runs `twmcp extract <file>` on an MCP JSON config and gets valid twmcp canonical TOML on stdout, with secrets replaced by `${VAR_NAME}` placeholders and unknown properties preserved as TOML comments.

**Independent Test**: Provide a Claude Desktop JSON config → verify stdout is valid TOML that `load_config` can parse.

### Tests for User Story 1

> **Write these tests FIRST, ensure they FAIL before implementation**

- [x] T002 [P] [US1] Write unit tests for `detect_servers()` in tests/test_extractor.py — test that mcpServers key is detected and servers dict is returned
- [x] T003 [P] [US1] Write unit tests for `is_secret_key()` in tests/test_extractor.py — test suffixes _TOKEN, _KEY, _SECRET, _PASSWORD, _CREDENTIALS (case-insensitive), and non-matching keys
- [x] T004 [P] [US1] Write unit tests for `normalize_type()` in tests/test_extractor.py — test "local"→"stdio", "stdio"→"stdio", "http"→"http", unknown types pass through
- [x] T005 [P] [US1] Write unit tests for TOML formatting in tests/test_extractor.py — test `format_server_toml()` produces correct TOML sections with command, args, type, env sub-table, headers sub-table, unknown props as comments, secret substitution in env/headers values
- [x] T006 [US1] Write integration test for full pipeline in tests/test_extractor.py — test `extract_from_file()` with tests/fixtures/claude_desktop.json, verify output is valid TOML with header comments listing secret placeholders

### Implementation for User Story 1

- [x] T007 [US1] Implement `detect_servers()`, `is_secret_key()`, `normalize_type()` in src/twmcp/extractor.py — detect_servers probes for mcpServers key (other formats added in US2), is_secret_key checks key-name suffixes, normalize_type maps "local"→"stdio"
- [x] T008 [US1] Implement `format_server_toml()` and `servers_to_toml()` in src/twmcp/extractor.py — per-server TOML string formatting with property ordering (command, args, type, url, tools, unknown-prop comments), env/headers sub-tables with secret placeholder substitution, header comment block with source file and secret variable list
- [x] T009 [US1] Implement `extract_from_file()` orchestrator in src/twmcp/extractor.py — reads JSON file, calls detect_servers, calls servers_to_toml, returns TOML string
- [x] T010 [US1] Add `extract` command to src/twmcp/cli.py — typer command taking file path argument, calls extract_from_file, prints result to stdout
- [x] T011 [US1] Write CLI test for `twmcp extract` success path in tests/test_cli.py — test via typer CliRunner, verify stdout contains valid TOML, exit code 0

**Checkpoint**: `twmcp extract tests/fixtures/claude_desktop.json` produces valid TOML on stdout. MVP complete.

---

## Phase 3: User Story 2 — Handle various MCP JSON formats (Priority: P2)

**Goal**: `twmcp extract` auto-detects and correctly handles Claude Desktop, VS Code, and flat/IntelliJ JSON structures.

**Independent Test**: Run extract against each format fixture → verify identical server data is extracted regardless of wrapper structure.

### Tests for User Story 2

- [x] T012 [P] [US2] Write test for VS Code format detection in tests/test_extractor.py — test `detect_servers()` with `{"mcp": {"servers": {...}}}` structure using tests/fixtures/vscode_mcp.json
- [x] T013 [P] [US2] Write test for flat/IntelliJ format detection in tests/test_extractor.py — test `detect_servers()` with `{"servers": {...}}` structure using tests/fixtures/flat_servers.json

### Implementation for User Story 2

- [x] T014 [US2] Extend `detect_servers()` in src/twmcp/extractor.py — add mcp.servers (VS Code) and servers (flat) detection branches after the mcpServers check

**Checkpoint**: `twmcp extract` works with all three JSON format variants.

---

## Phase 4: User Story 3 — Error reporting for invalid input (Priority: P3)

**Goal**: Clear, actionable error messages on stderr with exit code 1 for all failure modes.

**Independent Test**: Run extract with nonexistent file, broken JSON, and unrecognizable JSON → verify error messages match CLI contract.

### Tests for User Story 3

- [x] T015 [P] [US3] Write tests for error cases in tests/test_extractor.py — test extract_from_file with: nonexistent file (FileNotFoundError), invalid JSON (ValueError with parse details), valid JSON with no recognizable server structure (ValueError listing expected formats), empty servers dict (ValueError "no servers found")
- [x] T016 [US3] Write CLI tests for error output in tests/test_cli.py — test via CliRunner: verify error messages print to stderr, exit code is 1 for each error case

### Implementation for User Story 3

- [x] T017 [US3] Implement error handling in src/twmcp/extractor.py — raise FileNotFoundError for missing files, ValueError for invalid JSON (include parse error details), ValueError for no recognizable format (list expected keys), ValueError for empty servers
- [x] T018 [US3] Add error handling to `extract` command in src/twmcp/cli.py — catch exceptions from extract_from_file, print to stderr via typer.echo(err=True), raise typer.Exit(1)

**Checkpoint**: All error paths produce clear messages on stderr and exit with code 1.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validation and cleanup

- [x] T019 Verify round-trip: pipe `twmcp extract` output through `load_config` to confirm structural compatibility (FR-008, SC-003)
- [x] T020 Run `uv run python -m pytest tests/ --cov=twmcp` — verify 85% coverage minimum, fill gaps if needed
- [x] T021 Run `make lint` and `make format` — fix any issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on Setup (fixtures needed for tests)
- **US2 (Phase 3)**: Depends on US1 completion (extends detect_servers)
- **US3 (Phase 4)**: Depends on US1 completion (adds error handling to existing functions)
- **Polish (Phase 5)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Setup — delivers working MVP
- **US2 (P2)**: Depends on US1 — extends format detection in same function
- **US3 (P3)**: Depends on US1 — adds error paths to existing implementation

### Within Each User Story

- Tests MUST be written and FAIL before implementation begins
- Implementation follows test structure
- Story complete when all its tests pass

### Parallel Opportunities

Within Phase 2 (US1):
- T002, T003, T004, T005 can all run in parallel (different test functions, no deps)
- T007 and T008 can run in parallel (different functions in same file)

Within Phase 3 (US2):
- T012 and T013 can run in parallel (different fixtures, independent tests)

Within Phase 4 (US3):
- T015 and T016 can run in parallel (different test files)

---

## Parallel Example: User Story 1

```bash
# Launch all unit tests in parallel (T002-T005):
Task: "Write unit tests for detect_servers() in tests/test_extractor.py"
Task: "Write unit tests for is_secret_key() in tests/test_extractor.py"
Task: "Write unit tests for normalize_type() in tests/test_extractor.py"
Task: "Write unit tests for TOML formatting in tests/test_extractor.py"

# Then sequential implementation:
Task: "Implement detect_servers, is_secret_key, normalize_type in src/twmcp/extractor.py"
Task: "Implement format_server_toml and servers_to_toml in src/twmcp/extractor.py"
Task: "Implement extract_from_file orchestrator in src/twmcp/extractor.py"
Task: "Add extract command to src/twmcp/cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (fixture files)
2. Complete Phase 2: User Story 1 (tests → implementation)
3. **STOP and VALIDATE**: `twmcp extract tests/fixtures/claude_desktop.json` produces valid TOML
4. Functional MVP — can already convert mcpServers format

### Incremental Delivery

1. Setup + US1 → Working extraction for mcpServers format (MVP)
2. Add US2 → All three JSON format variants supported
3. Add US3 → Error handling for all failure modes
4. Polish → Coverage, linting, round-trip validation

---

## Notes

- [P] tasks = different files or functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution mandates TDD: write tests first, verify they fail, then implement
- All TOML generation is manual string formatting (no tomli_w) per research.md Decision 1
- Secret detection by key-name suffix per research.md Decision 4
- Format detection by probing known keys per research.md Decision 2
