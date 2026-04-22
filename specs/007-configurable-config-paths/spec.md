# Feature Specification: Configurable Agent Output Paths

**Feature Branch**: `007-configurable-config-paths`
**Created**: 2026-04-22
**Status**: Draft
**Input**: User description: "Make the target file location where `twmcp` writes each agent's MCP configuration user-configurable via `~/.config/twmcp/config.toml`, overriding the built-in defaults. `twmcp edit --init` must seed these defaults so users can discover and edit them."

## Clarifications

### Session 2026-04-22

- Q: How should a relative override path (e.g. `config_path = "foo/mcp.json"`) be resolved? → A: Resolve relative to current working directory (matches existing default behavior).
- Q: When `twmcp edit --init` runs but `config.toml` already exists, how is the new `[agents.*]` defaults block surfaced? → A: Keep existing behavior — `--init` refuses when file exists; users on an existing config must hand-merge or delete to regenerate.
- Q: What TOML schema shape should the override use? → A: `[agents.<name>] config_path = "..."` — one table per agent, mirrors the existing `[servers.<name>]` pattern and leaves room for additional per-agent keys later.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Override an agent's output path (Priority: P1)

A user wants `twmcp compile <agent>` to write to a non-default location (e.g. a different project folder, a dotfile-managed directory, or a platform-specific path on a non-macOS host) without forking `twmcp` or patching source.

**Why this priority**: This is the core value of the feature. Hard-coded paths block every user whose filesystem layout differs from the built-in assumptions — the default `claude-desktop` path only works on macOS, and project-local defaults like `.claude/mcp-config.json` may not match every team's layout. Without an override, these users cannot use `twmcp` at all.

**Independent Test**: Set a custom path for one agent in `~/.config/twmcp/config.toml`, run `twmcp compile <agent>`, and verify the output lands at the overridden path instead of the built-in default. The feature delivers value even if only a single agent override works.

**Acceptance Scenarios**:

1. **Given** a `config.toml` with `[agents.claude-code] config_path = "/tmp/custom/mcp.json"`, **When** the user runs `twmcp compile claude-code`, **Then** the compiled config is written to `/tmp/custom/mcp.json`, not to `.claude/mcp-config.json`.
2. **Given** a `config.toml` with no `[agents]` section, **When** the user runs `twmcp compile claude-code`, **Then** the built-in default path is used (backwards compatible).
3. **Given** a `config.toml` overriding only `claude-code`, **When** the user runs `twmcp compile copilot-cli`, **Then** `copilot-cli` still uses its built-in default.
4. **Given** an override path containing `~` or `${HOME}`, **When** `twmcp compile` runs, **Then** the path is expanded to the absolute user-home location before writing.

---

### User Story 2 - Discover and edit defaults via `edit --init` (Priority: P2)

A new user runs `twmcp edit --init` to create their config. The generated file already contains a commented `[agents.*]` block listing every known agent with its built-in default path, so the user can uncomment and tweak the one they want to change without reading source code or docs.

**Why this priority**: Without discoverability, the override mechanism (P1) exists but nobody finds it. Seeding defaults at init time is the documented, inline way users learn the feature.

**Independent Test**: Run `twmcp edit --init` in a clean environment; inspect the generated `config.toml`; confirm every agent from the registry appears with its correct built-in path, commented out.

**Acceptance Scenarios**:

1. **Given** no existing `~/.config/twmcp/config.toml`, **When** the user runs `twmcp edit --init`, **Then** the created file contains a commented `[agents.<name>]` block for every registered agent with `config_path` set to its built-in default.
2. **Given** the init-generated block is uncommented and modified, **When** the user runs `twmcp compile`, **Then** the overrides take effect.

---

### User Story 3 - Verify effective paths via `twmcp agents` (Priority: P3)

A user who has configured overrides wants to confirm which path `twmcp` will actually use for each agent without running `compile --dry-run`.

**Why this priority**: Quality-of-life. `compile --dry-run` already exposes the effective path, so this story is a convenience, not a blocker.

**Independent Test**: Configure an override, run `twmcp agents`, and confirm the listed path reflects the override (not the built-in default).

**Acceptance Scenarios**:

1. **Given** `[agents.claude-code] config_path = "/tmp/x.json"` in config, **When** the user runs `twmcp agents`, **Then** the `Config Path` column for `claude-code` shows `/tmp/x.json`.
2. **Given** no override for `intellij`, **When** the user runs `twmcp agents`, **Then** `intellij` still shows its built-in default.

---

### Edge Cases

- **Unknown agent key in config**: `[agents.does-not-exist] config_path = "..."` — must produce a clear error naming the unknown agent and listing valid agents, rather than silently ignoring the entry.
- **Relative vs absolute paths**: A relative override path resolves against the current working directory, matching today's behavior for defaults like `.claude/mcp-config.json`. This is the intuitive behavior for project-local setups.
- **`~` and `${VAR}` in override paths**: Must be expanded (user-home and environment variables) before the path is used for writing.
- **Override path points to a non-existent parent directory**: Parent directories are created automatically, matching current `compile` behavior.
- **Override value is not a string** (e.g. a table or integer): Must fail with a clear validation error identifying the offending key.
- **Running `edit --init` when `config.toml` already exists**: Keep existing behavior (refuse to overwrite); do not merge the defaults block into an existing file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The canonical configuration file MUST support an optional `[agents.<agent-name>]` section where `<agent-name>` matches a registered agent (`copilot-cli`, `intellij`, `claude-code`, `claude-desktop`, and any future additions).
- **FR-002**: Each `[agents.<agent-name>]` section MUST support a `config_path` key of type string that overrides the built-in output path for that agent.
- **FR-003**: When no override is present for an agent, the system MUST fall back to the built-in default path currently compiled into the agent registry.
- **FR-004**: Override paths MUST support `~` (home-directory) expansion and `${VAR}` / `${VAR:-default}` environment-variable interpolation consistent with the rest of the TOML config.
- **FR-005**: Overrides MUST take effect for all commands that consume agent output paths, including `twmcp compile`, `twmcp compile --all`, and `twmcp agents` (display).
- **FR-006**: An override referring to an agent name not present in the registry MUST cause a validation error that names the offending key and lists valid agents.
- **FR-007**: An override `config_path` whose value is not a string MUST cause a validation error that names the offending key and its actual type.
- **FR-008**: `twmcp edit --init` MUST write a `config.toml` that includes a commented block for every registered agent, each showing the agent's built-in default `config_path`, so the user can uncomment and edit any entry.
- **FR-009**: The init-generated agent block MUST remain valid TOML after being uncommented (no placeholder tokens, no syntactic scaffolding a user must remove).
- **FR-010**: Absence of the `[agents]` section MUST NOT cause errors or warnings — it is fully optional and everything continues to work with built-in defaults.
- **FR-011**: `twmcp agents` output MUST display the *effective* path (override if present, otherwise default) and MUST NOT require a separate flag to do so.

### Key Entities

- **AgentOverride**: A user-provided override for a single agent's output path. Attributes: agent name (must match the registry), `config_path` (string, may contain `~` and `${VAR}` placeholders). Belongs to the canonical configuration file alongside `[servers.*]` and `env_file`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can change where any single agent's MCP config is written by editing one line in `~/.config/twmcp/config.toml`, with no code changes and no `twmcp` reinstall.
- **SC-002**: `twmcp edit --init` on a clean system produces a file from which a user can enable a path override by uncommenting lines only — no typing of paths, agent names, or keys required.
- **SC-003**: Existing users who upgrade and do not modify their `config.toml` see zero behavioral change: every agent writes to exactly the same path as before.
- **SC-004**: Invalid override entries (unknown agent, wrong type) are rejected with an error message that lets the user fix the mistake without consulting documentation or source.
- **SC-005**: 100% of registered agents (present and future) are overridable through the same mechanism, with no per-agent special-casing required for users.

## Assumptions

- The existing `${VAR}` / `${VAR:-default}` interpolation applies uniformly — override paths are strings, so they flow through the same resolver as server fields.
- Relative override paths resolve against the current working directory, matching how today's defaults (`.claude/mcp-config.json`, `.copilot/mcp-config.json`) already behave. This is consistent and predictable for project-local setups.
- `twmcp edit --init` continues to refuse to overwrite an existing `config.toml`. Users who want the new defaults block must either delete their config or hand-merge — out of scope for this feature.
- The agent registry remains the single source of truth for the set of valid agent names; overrides validate against it.
- No new commands are introduced; this feature is purely additive to existing config and existing commands' behavior.
