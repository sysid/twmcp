# Feature Specification: MCP Config Compiler

**Feature Branch**: `001-mcp-config-compiler`
**Created**: 2026-02-17
**Status**: Draft
**Input**: User description: "Build a cli application which dynamically compiles the MCP configuration file for various agents, e.g. claude-code, copilot-cli. It has to respect agent specific configuration keys (if existent) and file location."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compile config for a single agent (Priority: P1)

A user maintains a single canonical list of MCP servers and wants to
generate the correctly formatted configuration file for a specific
agent (e.g. Copilot CLI). They run `twmcp compile copilot-cli` and
the tool reads the canonical server definitions, transforms them into
the agent's expected JSON structure (correct top-level key, type field
naming, header format), and writes the file to the agent's expected
location.

**Why this priority**: This is the core value proposition — one source
of truth, many targets. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by defining a sample canonical
config with 2-3 servers, running the compile command for one agent, and
verifying the output file matches the expected structure and location.

**Acceptance Scenarios**:

1. **Given** a canonical config with 3 MCP servers and a known agent
   "copilot-cli", **When** user runs `twmcp compile copilot-cli`,
   **Then** a valid JSON file is written to `~/.copilot/mcp-config.json`
   with `mcpServers` as the top-level key and each server correctly
   formatted.
2. **Given** a canonical config with servers, **When** user runs
   `twmcp compile copilot-cli --dry-run`, **Then** the compiled JSON is
   printed to stdout without writing any file.
3. **Given** an agent name that is not recognized, **When** user runs
   `twmcp compile unknown-agent`, **Then** the tool exits with a
   non-zero code and a clear error message listing available agents.

---

### User Story 2 - Compile config for all agents at once (Priority: P2)

A user wants to update all agent configs after adding a new MCP server.
They run `twmcp compile --all` and every supported agent gets its
config file regenerated from the canonical source.

**Why this priority**: Natural extension of P1 — bulk operation saves
time when managing multiple agents.

**Independent Test**: Can be tested by running `twmcp compile --all` and
verifying each agent's output file exists with correct structure.

**Acceptance Scenarios**:

1. **Given** a canonical config and 3 supported agents, **When** user
   runs `twmcp compile --all`, **Then** all 3 agent config files are
   written to their respective locations with correct formatting.
2. **Given** a canonical config, **When** user runs
   `twmcp compile --all --dry-run`, **Then** all compiled configs are
   printed to stdout (separated by agent name headers) without writing
   any files.

---

### User Story 3 - List supported agents and their config details (Priority: P3)

A user wants to see which agents are supported, where their config
files live, and what format they use. They run `twmcp agents` to get
a summary table.

**Why this priority**: Discovery and transparency — helps users
understand what the tool manages before they run compile.

**Independent Test**: Can be tested by running `twmcp agents` and
verifying the output lists all registered agents with their config
paths and top-level keys.

**Acceptance Scenarios**:

1. **Given** the tool has 3 registered agents, **When** user runs
   `twmcp agents`, **Then** a human-readable table is printed to stdout
   showing agent name, config file path, and top-level JSON key for
   each.
2. **Given** the tool has registered agents, **When** user runs
   `twmcp agents --json`, **Then** a JSON array is printed to stdout
   with the same information.

---

### User Story 4 - Interpolate variables during compilation (Priority: P2)

A user's canonical config contains placeholder references to secrets
and paths (e.g. API keys, token file paths) that differ per machine
or must not be stored in plaintext. During compilation, the tool
resolves these placeholders from environment variables or config files,
producing a compiled config with final concrete values.

**Why this priority**: Without interpolation, secrets must be hardcoded
in the canonical config — a security risk and portability problem. This
is essential for real-world use.

**Independent Test**: Can be tested by defining a canonical config with
placeholder references, setting the corresponding environment variables,
running compile, and verifying the output contains resolved values.

**Acceptance Scenarios**:

1. **Given** a canonical config with `${GITHUB_TOKEN}` in a server's
   env section and the environment variable `GITHUB_TOKEN` is set,
   **When** user runs `twmcp compile copilot-cli`, **Then** the
   compiled config contains the actual token value (not the placeholder).
2. **Given** a canonical config with `${API_KEY}` and the environment
   variable `API_KEY` is NOT set and no default is provided, **When**
   user runs `twmcp compile copilot-cli`, **Then** the tool exits with
   a non-zero code and an error listing the unresolved variable(s).
3. **Given** a canonical config with `${PORT:-8080}` (variable with
   default) and `PORT` is not set, **When** user runs
   `twmcp compile copilot-cli`, **Then** the compiled config contains
   `8080` as the resolved value.
4. **Given** a canonical config referencing a dotenv-style config file
   for variable values, **When** user runs `twmcp compile copilot-cli`,
   **Then** variables are resolved from that file, with environment
   variables taking precedence over file-defined values.

---

### Edge Cases

- What happens when the canonical config file does not exist or is
  empty? Tool MUST exit with a clear error and non-zero code.
- What happens when the target config file already exists? Tool MUST
  overwrite it (the canonical source is authoritative).
- What happens when the target directory does not exist? Tool MUST
  create intermediate directories.
- What happens when a canonical server entry uses fields not supported
  by a specific agent (e.g. `headers` for Claude Desktop which only
  supports stdio)? Tool MUST skip unsupported fields and optionally
  warn on stderr.
- What happens when the canonical config has syntax errors? Tool MUST
  report the parse error with file path and line/position if possible.
- What happens when a variable reference is undefined and has no
  default? Tool MUST fail with a clear error listing all unresolved
  variables (not just the first one).
- What happens when a referenced config/dotenv file does not exist?
  Tool MUST fail with a clear error naming the missing file.
- What happens with nested variable references (e.g. `${${PREFIX}_KEY}`)?
  Not supported in v1 — tool MUST treat the outer reference as a
  literal lookup and fail if not found.
- What happens when `--dry-run` is used with unresolved variables?
  Tool MUST still fail — dry-run previews the final output, which
  requires all variables resolved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read MCP server definitions from a single
  canonical configuration file.
- **FR-002**: System MUST compile the canonical config into
  agent-specific formats, respecting each agent's top-level JSON key
  (`mcpServers` vs `servers`), type field naming (`local`/`stdio`), and
  header structure (`headers` vs `requestInit.headers`).
- **FR-003**: System MUST write compiled config to each agent's expected
  file location (e.g. `~/.copilot/mcp-config.json`,
  `~/.config/github-copilot/intellij/mcp.json`).
- **FR-004**: System MUST support a `--dry-run` flag that prints output
  to stdout without writing files.
- **FR-005**: System MUST support compiling for a single named agent or
  all agents at once (`--all`).
- **FR-006**: System MUST list all supported agents with their config
  paths and format details.
- **FR-007**: System MUST support both human-readable and JSON output
  for informational commands.
- **FR-008**: System MUST validate the canonical config before
  compiling and report errors with context.
- **FR-009**: System MUST skip agent-specific fields that the target
  agent does not support, emitting a warning to stderr.
- **FR-010**: System MUST create intermediate directories if the target
  config path does not exist.
- **FR-011**: System MUST support agent-specific configuration keys
  that override or extend canonical server definitions for a particular
  agent. Overrides are inline in the canonical config as an optional
  `overrides` section per server, keyed by agent name.
- **FR-012**: System MUST resolve variable placeholders in canonical
  config values during compilation. Placeholder syntax: `${VAR_NAME}`.
- **FR-013**: System MUST resolve variables from environment variables.
- **FR-014**: System MUST support default values for variables using
  the syntax `${VAR_NAME:-default_value}`.
- **FR-015**: System MUST support loading variables from an external
  config file (dotenv-style key=value format). Environment variables
  take precedence over file-defined values.
- **FR-016**: System MUST fail with a clear error listing ALL
  unresolved variables if any placeholder cannot be resolved and has
  no default.

### Key Entities

- **Canonical Config**: The single-source-of-truth file defining all
  MCP servers with their connection details (command, args, env, url,
  headers, type). Format and location to be determined during planning.
- **Agent Profile**: A registered target agent with its name, config
  file path, top-level JSON key, supported server types, and field
  mapping rules.
- **Compiled Config**: The agent-specific JSON output derived from the
  canonical config by applying the agent profile's transformation rules.
- **Variable Reference**: A `${VAR_NAME}` placeholder in canonical
  config values that resolves to a concrete value from environment
  variables or a config file at compile time. Supports optional
  defaults via `${VAR_NAME:-default}`.

## Assumptions

- The canonical config format will be a superset of all agent-specific
  fields, using the most expressive structure as the base.
- Agent profiles are built into the tool (not user-configurable in
  v1). Adding a new agent requires a code change.
- The initial set of supported agents: Copilot CLI, IntelliJ Copilot,
  Claude Desktop.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can compile a config for any supported agent in a
  single command invocation.
- **SC-002**: Compiled config files are valid JSON that the target agent
  accepts without modification.
- **SC-003**: Adding a new MCP server to the canonical config and
  recompiling updates all agent configs correctly.
- **SC-004**: User can preview changes via `--dry-run` before any file
  is written.
- **SC-005**: All errors produce clear, actionable messages with
  non-zero exit codes.
- **SC-006**: Compiled configs contain resolved concrete values — no
  unresolved placeholders appear in any output file.
- **SC-007**: Secrets and machine-specific paths never need to be
  stored in the canonical config in plaintext.
