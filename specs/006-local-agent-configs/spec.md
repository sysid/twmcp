# Feature Specification: Project-Local Agent Configurations

**Feature Branch**: `006-local-agent-configs`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Add claude-code agent profile with project-local config `.claude/mcp-config.json`. Change copilot-cli agent to also use project-local config `.copilot/mcp-config.json`. Ensure correct syntax for each agent."

## Clarifications

### Session 2026-03-08

- Q: Should claude-code support http/sse servers with type field and flat headers (like copilot-cli), or skip them (like claude-desktop)? → A: Include type field, flat headers, support all server types (option B).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compile Claude Code MCP config (Priority: P1)

A user runs `twmcp compile claude-code` to generate a project-local MCP configuration file at `.claude/mcp-config.json` (relative to the current working directory). The generated file uses `mcpServers` as the top-level key, includes the `type` field, and renders headers in flat style. All server types (stdio, http, sse) are supported.

**Why this priority**: Claude Code is a heavily used AI coding agent that currently has no twmcp support at all. Adding it unblocks users from managing Claude Code MCP servers through the canonical config.

**Independent Test**: Can be fully tested by running `twmcp compile claude-code --dry-run` and verifying the output matches the expected Claude Code MCP JSON format, and by running without `--dry-run` and verifying the file is written to `.claude/mcp-config.json` in the current directory.

**Acceptance Scenarios**:

1. **Given** a valid canonical config with stdio servers, **When** user runs `twmcp compile claude-code`, **Then** a file `.claude/mcp-config.json` is created in the current working directory with the correct JSON structure.
2. **Given** a valid canonical config, **When** user runs `twmcp compile claude-code --dry-run`, **Then** the compiled JSON is printed to stdout and no file is written.
3. **Given** a canonical config with http servers and headers, **When** user runs `twmcp compile claude-code --dry-run`, **Then** the output includes the server with `type`, `url`, and flat `headers` fields.
4. **Given** the user runs `twmcp agents`, **Then** `claude-code` appears in the agent list with its config path shown as `.claude/mcp-config.json`.

---

### User Story 2 - Copilot CLI writes project-local config (Priority: P1)

The existing `copilot-cli` agent profile is changed so that it writes to `.copilot/mcp-config.json` (project-local, relative to CWD) instead of the global `~/.copilot/mcp-config.json`. The JSON format remains unchanged (same `mcpServers` key, `stdio→local` type mapping, flat header style).

**Why this priority**: Equally critical — the user explicitly requested this change. Moving to project-local configs gives users per-project MCP server control and avoids polluting global state.

**Independent Test**: Can be fully tested by running `twmcp compile copilot-cli` and verifying the output file is at `.copilot/mcp-config.json` relative to CWD, not at `~/.copilot/mcp-config.json`.

**Acceptance Scenarios**:

1. **Given** a valid canonical config, **When** user runs `twmcp compile copilot-cli`, **Then** the file is written to `.copilot/mcp-config.json` in the current working directory (not `~/.copilot/mcp-config.json`).
2. **Given** a valid canonical config with http servers with headers, **When** user runs `twmcp compile copilot-cli --dry-run`, **Then** headers appear in flat style and type mapping `stdio→local` is applied (existing behavior preserved).

---

### User Story 3 - Compile all includes claude-code (Priority: P2)

When user runs `twmcp compile --all`, the new `claude-code` agent is included alongside the existing agents, each writing to their respective config paths.

**Why this priority**: Follows naturally from P1 — once the profile exists, `--all` should include it. Lower priority because users can always compile individual agents.

**Independent Test**: Run `twmcp compile --all --dry-run` and verify claude-code output appears in the output.

**Acceptance Scenarios**:

1. **Given** a valid canonical config, **When** user runs `twmcp compile --all --dry-run`, **Then** output includes a `--- claude-code ---` section with correct JSON.

---

### Edge Cases

- What happens when the `.claude/` or `.copilot/` directory does not exist? The tool creates it (existing behavior of `write_config` which calls `mkdir(parents=True)`).
- What happens when a config file already exists at the target path? It is overwritten (existing behavior, no merge strategy needed).
- What happens when the canonical config contains http/sse servers and the target is claude-code? They are included with `type`, `url`, and flat `headers` fields (unlike claude-desktop which skips them).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST register a new agent profile named `claude-code` that writes to `.claude/mcp-config.json` relative to the current working directory.
- **FR-002**: The `claude-code` agent MUST use `mcpServers` as the top-level JSON key, include the `type` field, and use flat header style. All server types (stdio, http, sse) MUST be supported.
- **FR-003**: The `copilot-cli` agent profile MUST be changed to write to `.copilot/mcp-config.json` relative to the current working directory instead of the global `~/.copilot/mcp-config.json`.
- **FR-004**: The `copilot-cli` agent MUST retain its existing JSON format: `mcpServers` key, `stdio→local` type mapping, and flat header style.
- **FR-005**: The `twmcp agents` command MUST list `claude-code` with its project-local config path.
- **FR-006**: Both project-local agents MUST resolve their config path relative to the process's current working directory at the time of compilation.

### Key Entities

- **AgentProfile**: Existing dataclass extended to support project-local (relative) paths in addition to global (absolute) paths. The `config_path` field may now contain a relative `Path`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `twmcp compile claude-code` produces a valid MCP config file at `.claude/mcp-config.json` in the current directory.
- **SC-002**: Running `twmcp compile copilot-cli` produces a valid MCP config file at `.copilot/mcp-config.json` in the current directory (not the global home path).
- **SC-003**: All existing tests continue to pass after the changes.
- **SC-004**: Running `twmcp agents` lists 4 agents (copilot-cli, intellij, claude-desktop, claude-code) with correct paths.
