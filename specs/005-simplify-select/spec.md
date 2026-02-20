# Feature Specification: Simplify Select Options

**Feature Branch**: `005-simplify-select`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "Simplify --select by removing the Click monkey-patch complexity. Split into dedicated --interactive flag for interactive mode and --select for non-interactive server filtering only (including empty selection)."

## Clarifications

### Session 2026-02-20

- Q: How should "select zero servers" be expressed on the CLI? → A: `--select none` — a reserved keyword that is shell-safe, explicit, and readable in scripts.
- Q: Should `--select ""` (actual empty string) be an error or silently treated as `--select none`? → A: Error with message: "No server names provided. Use --select none for empty configuration."
- Q: What should happen with `--select none,github` (keyword mixed with server names)? → A: Error — `none` cannot be combined with server names. Must be used alone.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Non-Interactive Server Selection with --select (Priority: P1)

A user wants to compile configuration for a specific subset of servers in a script or CI pipeline. They pass `--select <names>` with a comma-separated list of server names. Only those servers appear in the compiled output.

**Why this priority**: This is the core non-interactive use case and the most common automation scenario. It must work reliably without any interactive terminal.

**Independent Test**: Can be fully tested by running `twmcp compile copilot-cli --select github,local-proxy --dry-run` and verifying only the specified servers appear in the JSON output.

**Acceptance Scenarios**:

1. **Given** a config with servers `github`, `atlassian`, `local-proxy`, **When** `--select github,local-proxy` is passed, **Then** only `github` and `local-proxy` appear in the compiled output.
2. **Given** a config with servers, **When** `--select nonexistent` is passed, **Then** the command exits with error code 1 and lists available servers.
3. **Given** a config with servers, **When** `--select github` is passed with `--all`, **Then** all agents are compiled but each only includes the `github` server.

---

### User Story 2 - Empty Non-Interactive Selection with --select none (Priority: P1)

A user wants to compile a configuration with zero servers selected (e.g., to produce an empty MCP configuration for a clean state). They pass `--select none` to explicitly request an empty selection using the reserved keyword.

**Why this priority**: This is the key motivator for the change -- the current implementation cannot support empty selection. Equal priority with US1 as it represents the primary gap being fixed.

**Independent Test**: Can be fully tested by running `twmcp compile copilot-cli --select none --dry-run` and verifying the output contains an empty server map.

**Acceptance Scenarios**:

1. **Given** a config with servers, **When** `--select none` is passed, **Then** the compiled output contains an empty server map (e.g., `{"mcpServers": {}}`).
2. **Given** a config with servers, **When** `--select none` is passed with `--all --dry-run`, **Then** all agents are compiled with empty server maps.
3. **Given** a config with a server literally named `none`, **When** `--select none` is passed, **Then** the reserved keyword takes precedence and an empty server map is produced (the keyword `none` is documented as reserved).
4. **Given** a config with servers, **When** `--select ""` (empty string) is passed, **Then** the command exits with error code 1 and a message suggesting `--select none`.

---

### User Story 3 - Interactive Server Selection with --interactive (Priority: P2)

A user at a terminal wants to interactively pick which servers to include. They pass `--interactive` and get a multi-select menu. After selecting, only chosen servers appear in the output.

**Why this priority**: Interactive mode is valuable but used less frequently than scripted/non-interactive mode. It requires a dedicated terminal.

**Independent Test**: Can be tested by mocking the interactive prompt and verifying the correct servers are passed through.

**Acceptance Scenarios**:

1. **Given** a user at an interactive terminal, **When** `--interactive` is passed, **Then** a multi-select menu appears showing all available servers.
2. **Given** a user at an interactive terminal, **When** `--interactive` is passed and the user selects `github` and `local-proxy`, **Then** only those servers appear in the output.
3. **Given** a user at an interactive terminal, **When** `--interactive` is passed and the user presses Escape, **Then** the command exits cleanly with code 0.
4. **Given** a user at an interactive terminal, **When** `--interactive` is passed and the user confirms without selecting anything, **Then** the compiled output contains an empty server map.
5. **Given** a non-interactive environment (piped stdin), **When** `--interactive` is passed, **Then** the command exits with error code 1 and an appropriate message.

---

### User Story 4 - Mutual Exclusivity of --select and --interactive (Priority: P2)

A user accidentally passes both `--select` and `--interactive`. The CLI rejects this combination with a clear error message.

**Why this priority**: Important for correctness and clear UX, but a guard rail rather than core functionality.

**Independent Test**: Can be tested by passing both flags and verifying an error is returned.

**Acceptance Scenarios**:

1. **Given** any configuration, **When** both `--select github` and `--interactive` are passed, **Then** the command exits with error code 1 and a message explaining the options are mutually exclusive.

---

### User Story 5 - Removal of Click Monkey-Patch Complexity (Priority: P1)

The codebase no longer contains the `_apply_select_patch`, `_install_select_patch` functions, or the `_INTERACTIVE` sentinel. The `--select` option is a standard typer `Option` with no Click-level modifications.

**Why this priority**: This is the core motivation for the refactoring -- eliminating fragile internal patches that create maintenance burden and testing complexity.

**Independent Test**: Can be verified by inspecting the code and confirming no monkey-patching functions remain. Existing tests pass without the patch infrastructure.

**Acceptance Scenarios**:

1. **Given** the refactored codebase, **When** the source is inspected, **Then** no `_flag_needs_value`, `_apply_select_patch`, or `_install_select_patch` references exist.
2. **Given** the refactored codebase, **When** all existing tests are run, **Then** all tests pass (with test updates to reflect the new `--interactive` flag).

---

### Edge Cases

- What happens when `--select` is passed without a value? Standard typer behavior: error about missing value.
- What happens when `--select ""` (empty string) is passed? Error with message suggesting `--select none`. Prevents silent misconfiguration from unset shell variables.
- What happens when `--select " , , "` is passed (only whitespace/commas)? Error — no valid server names provided. Use `--select none` for explicit empty selection.
- What happens when `--interactive` is passed with `--all`? Works correctly: interactive prompt shown once, selection applied to all agents.
- What happens when `--select none,github` is passed? Error — `none` is a reserved keyword and cannot be combined with server names.
- What happens when neither `--select` nor `--interactive` is passed? All servers are included (current default behavior, unchanged).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `--select <value>` option that accepts a comma-separated list of server names for non-interactive filtering.
- **FR-002**: System MUST accept `--select none` (reserved keyword) to produce a configuration with zero servers. The keyword `none` is case-sensitive and reserved.
- **FR-003**: System MUST provide an `--interactive` boolean flag that launches a terminal-based multi-select menu.
- **FR-004**: System MUST reject the combination of `--select` and `--interactive` with a clear error message and exit code 1.
- **FR-005**: System MUST reject `--interactive` when stdin is not connected to an interactive terminal.
- **FR-006**: System MUST NOT contain any Click/typer monkey-patching code (`_flag_needs_value`, `_apply_select_patch`, `_install_select_patch`, `_INTERACTIVE` sentinel).
- **FR-007**: System MUST reject `--select` with only whitespace/commas (e.g., `--select " , , "`) as an error. Users must use `--select none` for explicit empty selection.
- **FR-008**: System MUST validate server names passed to `--select` against the available servers in the configuration and report unknown names with suggestions.
- **FR-009**: System MUST reject `--select none,<names>` (reserved keyword mixed with server names) with an error explaining `none` must be used alone.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can produce an empty configuration via `--select none` in a single command invocation.
- **SC-002**: All existing server selection functionality (interactive and non-interactive) works correctly with the new flag structure.
- **SC-003**: The codebase contains zero lines of Click/typer monkey-patching code after refactoring.
- **SC-004**: All tests pass, including updated tests reflecting the new `--interactive` / `--select` separation.
- **SC-005**: The `--interactive` and `--select` flags are mutually exclusive and the CLI clearly communicates this constraint.

## Assumptions

- The `simple-term-menu` dependency remains for the interactive prompt (no change).
- The `--select` option remains a standard typer `Option[str]` with `None` as default (no selection = all servers).
- The `--interactive` flag is a standard typer boolean `Option` defaulting to `False`.
- Backward compatibility for `--select <names>` (non-interactive with values) is preserved. Only the bare `--select` (without value) behavior changes -- it is no longer supported; users must use `--interactive` instead.
- The `parse_select_value` function in `selector.py` will be updated to recognize `none` as a reserved keyword returning an empty list. It continues to reject empty/whitespace-only input as an error.
