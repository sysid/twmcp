# Feature Specification: Interactive MCP Server Selection

**Feature Branch**: `002-interactive-server-select`
**Created**: 2026-02-18
**Status**: Draft
**Input**: User description: "the user should be able to interactively select the mcp servers which should be actived in the compile command"

## Clarifications

### Session 2026-02-18

- Q: Should `--select` be interactive-only, or also accept an inline comma-separated value for non-interactive filtering? → A: Dual-mode — interactive when bare (`--select`), non-interactive filter when given a value (`--select github,local-proxy`).
- Q: What information should each entry in the interactive multi-select prompt display? → A: Server name + type (e.g., `github [stdio]`, `atlassian [http]`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Server Selection During Compile (Priority: P1)

A user runs the `compile` command for a specific agent and is presented with a list of all MCP servers defined in the canonical config. They can interactively select which servers to include in the compiled output. Only the selected servers appear in the resulting agent configuration.

**Why this priority**: This is the core feature. Without interactive selection, the user has no way to control which servers are included per compile run — they get all-or-nothing.

**Independent Test**: Can be fully tested by running `twmcp compile copilot-cli --select` and verifying that an interactive prompt appears listing all servers, allowing the user to toggle individual servers on/off, and producing output containing only the selected servers.

**Acceptance Scenarios**:

1. **Given** a config with 3 servers (github, atlassian, local-proxy), **When** the user runs `twmcp compile copilot-cli --select`, **Then** an interactive multi-select prompt appears listing all 3 servers with name and type (e.g., `github [stdio]`, `atlassian [http]`, `local-proxy [stdio]`).
2. **Given** the interactive prompt is displayed, **When** the user selects only "github" and "local-proxy", **Then** the compiled JSON output contains only those 2 servers and omits "atlassian".
3. **Given** the interactive prompt is displayed, **When** the user selects no servers, **Then** the system informs the user that no servers were selected and exits without writing a config file.
4. **Given** the interactive prompt is displayed, **When** the user cancels (Ctrl+C / Escape), **Then** the command exits cleanly without writing any files and without an error traceback.

---

### User Story 2 - Non-Interactive Server Filtering via --select (Priority: P2)

A user runs the `compile` command with `--select` followed by a comma-separated list of server names. The system skips the interactive prompt and compiles only the specified servers. This supports scripting and automation use cases.

**Why this priority**: Enables non-interactive workflows (CI/CD, shell scripts, aliases) to select a subset of servers without human interaction. Builds naturally on the P1 flag.

**Independent Test**: Can be tested by running `twmcp compile copilot-cli --select github,local-proxy --dry-run` and verifying that no interactive prompt appears and only the named servers are in the output.

**Acceptance Scenarios**:

1. **Given** a config with 3 servers, **When** the user runs `twmcp compile copilot-cli --select github,local-proxy`, **Then** no interactive prompt appears and the compiled output contains only "github" and "local-proxy".
2. **Given** the user specifies `--select unknown-server`, **When** the command runs, **Then** the system reports an error listing the unrecognized server name(s) and the available server names, then exits without writing files.
3. **Given** the user specifies `--select github`, **When** combined with `--all`, **Then** all agents receive only the "github" server (subject to agent compatibility filtering).

---

### User Story 3 - Interactive Selection with --all Flag (Priority: P3)

A user runs the `compile --all --select` command to compile for all registered agents, with interactive server selection applied consistently across all agent outputs.

**Why this priority**: Extends the P1/P2 capability to the `--all` workflow so users can batch-compile for every agent while still controlling which servers are included.

**Independent Test**: Can be tested by running `twmcp compile --all --select --dry-run` and verifying the prompt appears once, and all agent outputs respect the same server selection.

**Acceptance Scenarios**:

1. **Given** a config with 3 servers and 3 registered agents, **When** the user runs `twmcp compile --all --select`, **Then** the interactive prompt appears once (not once per agent).
2. **Given** the user selected "github" and "local-proxy" in the prompt, **When** compilation runs for each agent, **Then** every agent's output contains only the selected servers (subject to existing agent compatibility rules).
3. **Given** a server is selected but incompatible with a specific agent (e.g., HTTP server for claude-desktop), **When** compilation runs, **Then** that server is still skipped for the incompatible agent with the existing warning, and other selected servers are included.

---

### User Story 4 - Non-Interactive Default Behavior Preserved (Priority: P4)

When the user does not pass the `--select` flag, the compile command behaves exactly as it does today — all servers are included by default with no interactive prompt.

**Why this priority**: Backward compatibility is essential. Existing scripts and workflows must not break.

**Independent Test**: Can be tested by running `twmcp compile copilot-cli --dry-run` (without `--select`) and verifying no interactive prompt appears and all servers are present in the output — identical to current behavior.

**Acceptance Scenarios**:

1. **Given** a config with 3 servers, **When** the user runs `twmcp compile copilot-cli` without `--select`, **Then** no interactive prompt appears and all compatible servers are included in the output.
2. **Given** the compile command is invoked programmatically (e.g., in a script), **When** `--select` is not used, **Then** the command runs non-interactively and produces the same output as before this feature existed.

---

### Edge Cases

- What happens when the config contains only 1 server and `--select` is used without a value? The prompt still appears, showing 1 server pre-selected.
- What happens when stdin is not a TTY (e.g., piped input) and `--select` is used without a value? The system detects non-interactive mode and exits with a clear error message telling the user that `--select` without a value requires an interactive terminal.
- What happens when all selected servers are incompatible with the target agent? The system produces an empty server list with a warning, consistent with current behavior when no servers survive filtering.
- What happens when `--select` is given a value containing an unrecognized server name mixed with valid ones (e.g., `--select github,typo-server`)? The system reports the unrecognized name(s), lists available servers, and exits without writing files (fail-fast, no partial output).
- What happens when `--select` is given with an empty string value? The system treats it as an error and exits with a message indicating no servers were specified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `--select` flag on the `compile` command that operates in two modes: interactive (no value) and non-interactive (comma-separated server names).
- **FR-002**: System MUST display all servers defined in the canonical config as selectable options in interactive mode, showing server name and type (e.g., `github [stdio]`, `atlassian [http]`).
- **FR-003**: System MUST allow the user to select or deselect individual servers via a multi-select prompt in interactive mode.
- **FR-004**: System MUST compile only the user-selected servers (from either mode) into the agent-specific output.
- **FR-005**: System MUST show all servers as pre-selected by default when the interactive prompt appears (opt-out model).
- **FR-006**: System MUST handle user cancellation (Ctrl+C / Escape) gracefully in interactive mode — no files written, no error traceback.
- **FR-007**: System MUST display an informational message and exit cleanly when the user selects zero servers (interactive mode).
- **FR-008**: System MUST present the selection prompt exactly once when `--select` (without value) is combined with `--all`, applying the same selection across all agents.
- **FR-009**: System MUST preserve existing compile behavior (all servers included, no prompt) when `--select` is not passed.
- **FR-010**: System MUST detect non-interactive terminals (stdin is not a TTY) when `--select` is used without a value and exit with a descriptive error message.
- **FR-011**: System MUST validate all server names provided via `--select <value>` against the canonical config and report unrecognized names with a list of available servers, exiting without writing files.
- **FR-012**: System MUST skip the interactive prompt when `--select` is given a comma-separated value, using the provided names directly.

### Key Entities

- **Server Selection**: The set of server names chosen by the user, either interactively via prompt or non-interactively via comma-separated value. This is a transient per-invocation concept — it is not persisted.
- **Canonical Config (existing)**: The TOML configuration containing all MCP server definitions. Unchanged by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select specific servers from the full list in under 10 seconds for configs with up to 20 servers.
- **SC-002**: 100% of existing `compile` invocations without `--select` produce identical output to pre-feature behavior.
- **SC-003**: Users successfully complete the selection flow on first attempt without needing documentation (intuitive prompt design).
- **SC-004**: The command exits within 1 second of user cancellation with no residual effects (no partial files written).
- **SC-005**: Non-interactive `--select <value>` mode produces correct output for valid server names and clear error messages for invalid names.

## Assumptions

- The interactive prompt will be opt-in via `--select` flag (not default behavior) to preserve backward compatibility and scriptability.
- All servers are pre-selected by default in the prompt (opt-out model), since the common case is excluding a few servers rather than cherry-picking from many.
- The selection prompt is shown once even with `--all` because the server list is agent-independent (agents may still filter incompatible servers afterward).
- The feature only affects which servers are compiled — it does not change how individual servers are compiled (overrides, type mappings, etc. still apply).
- Server names in `--select <value>` are comma-separated without spaces (e.g., `github,local-proxy`). If a name contains a comma, this is unsupported (no server names in the current config contain commas).
