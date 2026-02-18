# Feature Specification: MCP Config to TOML Converter

**Feature Branch**: `003-mcp-to-toml`
**Created**: 2026-02-18
**Status**: Draft
**Input**: User description: "create a sample toml configuration printed to stdout from a given mcp configuration file, e.g. mcp-config.json"

## Clarifications

### Session 2026-02-18

- Q: What should the CLI command name be for this feature? → A: `twmcp extract <file>` — "extract" communicates the directionality of pulling TOML from a JSON config.
- Q: How should unknown JSON properties (not in twmcp's model) be handled? → A: Preserve as TOML comments (e.g., `# unknown: disabled = true`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract canonical TOML from MCP JSON (Priority: P1)

A user has an existing MCP configuration file (e.g., the standard `mcp-config.json` used by Claude Desktop or VS Code) and wants to onboard it into twmcp. They run `twmcp extract <file>` pointing at their JSON file and receive a valid twmcp canonical TOML configuration printed to stdout, ready to be saved or piped into a file.

**Why this priority**: This is the core feature — without it, users must manually translate their existing MCP configs into TOML, which is tedious and error-prone. This removes the primary barrier to twmcp adoption.

**Independent Test**: Can be fully tested by providing any valid MCP JSON config file and verifying the stdout output is valid, parseable TOML that twmcp can load.

**Acceptance Scenarios**:

1. **Given** a valid MCP JSON config file with stdio-type servers, **When** the user runs `twmcp extract <file>`, **Then** the tool prints valid twmcp canonical TOML to stdout containing all servers with their commands, args, and environment variables.
2. **Given** a valid MCP JSON config file with a top-level wrapper key (e.g., `"mcpServers"` or `"mcp"` with nested `"servers"`), **When** the user runs `twmcp extract <file>`, **Then** the tool correctly extracts the servers regardless of the wrapper structure.
3. **Given** a valid MCP JSON config file containing environment variable values, **When** the user runs `twmcp extract <file>`, **Then** literal secret values are replaced with `${VAR_NAME}` placeholder references in the TOML output, and a comment notes which variables need to be set.

---

### User Story 2 - Handle various MCP JSON formats (Priority: P2)

Different tools produce MCP config files with different structures. Claude Desktop uses `{"mcpServers": {...}}`, VS Code uses `{"mcp": {"servers": {...}}}`, and some tools use a flat `{"servers": {...}}` structure. The converter should recognize and handle these common variants.

**Why this priority**: Without format flexibility, users would need to manually restructure their JSON before converting, defeating the purpose of the tool.

**Independent Test**: Can be tested by providing JSON files in each known format variant and verifying correct TOML output for each.

**Acceptance Scenarios**:

1. **Given** a Claude Desktop format JSON (`{"mcpServers": {...}}`), **When** the user runs `twmcp extract <file>`, **Then** the servers are correctly extracted and converted.
2. **Given** a VS Code format JSON (`{"mcp": {"servers": {...}}}`), **When** the user runs `twmcp extract <file>`, **Then** the servers are correctly extracted and converted.
3. **Given** a flat format JSON (`{"servers": {...}}`), **When** the user runs `twmcp extract <file>`, **Then** the servers are correctly extracted and converted.

---

### User Story 3 - Error reporting for invalid input (Priority: P3)

When the user provides an invalid or unrecognizable file, they receive clear error messages explaining what went wrong and what formats are supported.

**Why this priority**: Good error messages reduce friction and support self-service troubleshooting.

**Independent Test**: Can be tested by providing malformed JSON, non-JSON files, and JSON without recognizable server structures, verifying clear error messages.

**Acceptance Scenarios**:

1. **Given** a file that is not valid JSON, **When** the user runs `twmcp extract <file>`, **Then** the tool prints a clear error message indicating the JSON is malformed and exits with a non-zero status code.
2. **Given** a valid JSON file with no recognizable MCP server structure, **When** the user runs `twmcp extract <file>`, **Then** the tool prints an error listing the expected formats it searched for and exits with a non-zero status code.
3. **Given** a file path that does not exist, **When** the user runs `twmcp extract <file>`, **Then** the tool prints a clear "file not found" error and exits with a non-zero status code.

---

### Edge Cases

- What happens when the JSON contains server types not supported by twmcp (e.g., unknown transport types)? The converter includes them as-is with a TOML comment noting the unrecognized type.
- What happens when a server entry has no `command` field (e.g., SSE/HTTP servers with only a `url`)? The converter handles URL-based servers correctly, mapping them to `type = "http"` with the `url` field.
- What happens when environment variable values in the JSON contain actual secrets (API keys, tokens)? The converter detects common patterns (keys ending in `_TOKEN`, `_KEY`, `_SECRET`, `_PASSWORD`) and replaces their values with `${VAR_NAME}` placeholders.
- What happens when the JSON file is empty or contains an empty servers object? The tool reports that no servers were found.
- What happens when the JSON contains properties not in twmcp's data model (e.g., `"disabled": true`)? The converter preserves them as TOML comments (e.g., `# unknown: disabled = true`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a file path to an MCP JSON configuration file as input via `twmcp extract <file>`.
- **FR-002**: System MUST auto-detect the JSON structure variant (Claude Desktop `mcpServers`, VS Code `mcp.servers`, or flat `servers` key) without requiring user specification.
- **FR-003**: System MUST convert each discovered server entry into twmcp canonical TOML `[servers.<name>]` format.
- **FR-004**: System MUST print the resulting TOML configuration to stdout.
- **FR-005**: System MUST map server properties correctly: `command`, `args`, `env`, `type`, `url`, `headers`.
- **FR-006**: System MUST detect environment variable values matching common secret patterns (`*_TOKEN`, `*_KEY`, `*_SECRET`, `*_PASSWORD`) and replace them with `${VAR_NAME}` placeholder syntax.
- **FR-007**: System MUST exit with a non-zero status code on any error (invalid JSON, file not found, no servers found).
- **FR-008**: System MUST produce TOML output that can be loaded by twmcp's existing `load_config` function without modification (aside from resolving placeholders).
- **FR-009**: System MUST preserve unrecognized JSON properties as TOML comments in the output.

### Key Entities

- **MCP JSON Config**: The input file in one of several known JSON structures containing MCP server definitions. Key attributes: server name, command, args, env, type, url, headers.
- **Canonical TOML Config**: The output format matching twmcp's existing `[servers.<name>]` structure with optional `env_file`, variable placeholders, and server properties.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can convert any standard MCP JSON config file to valid twmcp TOML via `twmcp extract <file>` in a single command invocation.
- **SC-002**: 100% of server entries present in the input JSON appear in the generated TOML output.
- **SC-003**: The generated TOML output is parseable by twmcp's existing configuration loader without structural errors.
- **SC-004**: Sensitive values (tokens, keys, passwords) are replaced with placeholder references in 100% of cases where they match the detection pattern.
- **SC-005**: Users receive actionable error messages for all failure modes (invalid JSON, missing file, no servers) within 1 second of invocation.

## Assumptions

- The input file is a local file (no remote URL fetching required).
- The most common MCP JSON formats are: Claude Desktop (`mcpServers`), VS Code (`mcp.servers`), and flat (`servers`). Other formats are out of scope for initial implementation.
- Secret detection uses key-name pattern matching (suffix-based), not value inspection. This is a heuristic and may not catch all secrets.
- The generated TOML does not include an `env_file` directive — users add that manually if desired.
- The `overrides` section (agent-specific customizations) is not populated by the converter since the input JSON represents a single agent's config.

## Scope Boundaries

**In scope**:
- Reading and parsing MCP JSON config files
- Auto-detecting JSON structure variants
- Converting to twmcp canonical TOML format
- Secret placeholder substitution
- Preserving unknown properties as TOML comments
- Stdout output
- Error handling and reporting

**Out of scope**:
- Writing output directly to a file (users can redirect stdout)
- Importing multiple JSON files at once
- Generating `overrides` sections
- Round-trip fidelity (converting TOML back to the original JSON format)
- Remote file fetching
