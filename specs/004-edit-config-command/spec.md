# Feature Specification: Edit Config Command

**Feature Branch**: `004-edit-config-command`
**Created**: 2026-02-18
**Status**: Draft
**Input**: User description: "Create an edit command to edit the canonical configuration with the default EDITOR. Add a --init option to create a new configuration with sensible defaults, but make sure existing configuration is not blindly overwritten"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open Config in Editor (Priority: P1)

A user runs `twmcp edit` to open their canonical configuration file in their preferred text editor. The system launches the editor specified by the `$EDITOR` environment variable (falling back to `$VISUAL`, then a sensible platform default). When the editor exits, the user returns to the shell prompt.

**Why this priority**: This is the core functionality of the command. Without it, nothing else matters.

**Independent Test**: Can be tested by running `twmcp edit` with a known config file and verifying the editor is launched with the correct file path.

**Acceptance Scenarios**:

1. **Given** a canonical config exists at the default location and `$EDITOR` is set, **When** the user runs `twmcp edit`, **Then** the system opens the config file in the editor specified by `$EDITOR`.
2. **Given** a canonical config exists at the default location and `$EDITOR` is not set but `$VISUAL` is, **When** the user runs `twmcp edit`, **Then** the system opens the config file in the editor specified by `$VISUAL`.
3. **Given** neither `$EDITOR` nor `$VISUAL` is set, **When** the user runs `twmcp edit`, **Then** the system falls back to a platform default editor (e.g., `vi`).
4. **Given** a canonical config exists at a custom path, **When** the user runs `twmcp edit --config /path/to/config.toml`, **Then** the system opens that specific file in the editor.

---

### User Story 2 - Initialize New Config (Priority: P1)

A user who does not yet have a configuration file runs `twmcp edit --init` to create one with sensible defaults. The system generates a well-commented starter configuration at the default location and then opens it in the editor.

**Why this priority**: Equal to P1 because new users need a way to bootstrap their configuration. Without `--init`, users must manually create a TOML file from scratch.

**Independent Test**: Can be tested by running `twmcp edit --init` in a clean environment (no existing config) and verifying a valid default config is created and opened in the editor.

**Acceptance Scenarios**:

1. **Given** no config file exists at the default location, **When** the user runs `twmcp edit --init`, **Then** the system creates a default config file with sensible defaults and opens it in the editor.
2. **Given** the parent directory for the config does not exist, **When** the user runs `twmcp edit --init`, **Then** the system creates the directory structure before writing the file.

---

### User Story 3 - Protect Existing Config from Overwrite (Priority: P1)

A user who already has a configuration file runs `twmcp edit --init` by mistake. The system refuses to overwrite the existing file and informs the user.

**Why this priority**: Data safety is critical. Silently overwriting a user's carefully crafted configuration would be destructive and irreversible.

**Independent Test**: Can be tested by running `twmcp edit --init` when a config already exists and verifying it exits with an error message without modifying the file.

**Acceptance Scenarios**:

1. **Given** a config file already exists at the default location, **When** the user runs `twmcp edit --init`, **Then** the system prints an error message indicating the file exists, does not modify it, and exits with a non-zero exit code.
2. **Given** a config file already exists at a custom path, **When** the user runs `twmcp edit --init --config /path/to/config.toml`, **Then** the same protection applies.
3. **Given** `--init` is used and the file exists, **When** the user sees the error, **Then** the message suggests using `twmcp edit` (without `--init`) to edit the existing file.

---

### Edge Cases

- What happens when the config file path is not writable (permission denied)? The system reports a clear filesystem error and exits with a non-zero code.
- What happens when `$EDITOR` points to a non-existent program? The system reports that the editor was not found and exits with a non-zero code.
- What happens when the editor exits with a non-zero exit code? The system propagates the exit code without additional error messaging (the editor may have its own reasons).
- What happens when `twmcp edit` is run but no config file exists and `--init` is not specified? The system exits with an error suggesting the user run `twmcp edit --init`.
- What happens when `twmcp edit --init` is used with `--config` pointing to a path where the file does not exist but the directory does? The system creates the file normally (directory creation is only needed when the directory is also absent).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an `edit` subcommand that opens the canonical config file in the user's preferred editor.
- **FR-002**: System MUST resolve the editor using this precedence: `$EDITOR` > `$VISUAL` > platform default (`vi`).
- **FR-003**: System MUST support a `--config` option to specify an alternative config file path (consistent with the existing `compile` command).
- **FR-004**: System MUST support an `--init` flag that creates a new config file with sensible defaults.
- **FR-005**: The default config created by `--init` MUST be valid TOML and include comments explaining each section.
- **FR-006**: System MUST NOT overwrite an existing config file when `--init` is used. It MUST exit with an error and a helpful message.
- **FR-007**: System MUST create parent directories as needed when `--init` creates a new config file.
- **FR-008**: When `twmcp edit` is run without `--init` and no config file exists, the system MUST exit with an error suggesting the user run `twmcp edit --init`.
- **FR-009**: System MUST report a clear error when the editor command fails to launch or is not found.

### Key Entities

- **Canonical Config File**: The TOML configuration file at `~/.config/twmcp/config.toml` (default) that defines MCP server entries.
- **Default Template**: A starter TOML configuration with commented examples demonstrating common server configurations (stdio, http types).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can open their config for editing in a single command (`twmcp edit`) without needing to remember the config file path.
- **SC-002**: New users can bootstrap a working configuration in under 30 seconds using `twmcp edit --init`.
- **SC-003**: No existing configuration is ever lost or overwritten by the `--init` flag.
- **SC-004**: The generated default config is valid and parseable by the existing `twmcp compile` command without modification (after the user adds their actual server entries).

## Assumptions

- The `--config` option follows the same default path convention as the existing `compile` command (`~/.config/twmcp/config.toml`).
- The platform default editor fallback (`vi`) is acceptable for Unix-like systems. Windows is not a supported platform for this tool.
- The default template config should include commented-out example servers (stdio and http types) to guide the user, rather than active server definitions that would fail without real credentials.
- The `edit` command runs the editor as a foreground subprocess and waits for it to exit before returning.
