# Research: MCP Config Compiler

**Date**: 2026-02-17
**Branch**: `001-mcp-config-compiler`

## Agent Config Format Analysis

Analyzed actual config files on the system.

### Copilot CLI

- **File**: `~/.copilot/mcp-config.json`
- **Top-level key**: `mcpServers`
- **Server types**: `local` (for stdio), `http`
- **Headers**: flat `"headers": {"key": "value"}`
- **Extra fields**: `tools` (array, e.g. `["*"]`)

### IntelliJ Copilot

- **File**: `~/.config/github-copilot/intellij/mcp.json`
- **Top-level key**: `servers`
- **Server types**: `stdio`, `http`, `sse`
- **Headers**: nested `"requestInit": {"headers": {"key": "value"}}`
- **Note**: File contains `//` comments (JSON5-style, not valid JSON).
  When we write output for this agent we MUST produce valid JSON
  (no comments). Existing file content will be fully replaced.

### Claude Desktop

- **File**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Top-level key**: `mcpServers`
- **Server types**: `stdio` (implied, no type field needed)
- **Note**: Not present on this system. Format documented by Anthropic.

### Key Differences Summary

| Field         | Copilot CLI       | IntelliJ          | Claude Desktop    |
|---------------|-------------------|-------------------|-------------------|
| Top-level key | `mcpServers`      | `servers`         | `mcpServers`      |
| stdio type    | `local`           | `stdio`           | (omitted)         |
| http headers  | `headers: {}`     | `requestInit.headers: {}` | N/A        |
| tools field   | supported         | not observed      | not supported     |
| env field     | supported         | supported         | supported         |

## Technology Decisions

### Decision: Canonical config format → TOML

**Rationale**: Python 3.13+ includes `tomllib` in stdlib (zero
dependencies). TOML is more readable than JSON for hand-edited config
files, supports comments natively, and Tom already uses it extensively
(pyproject.toml). The canonical config is hand-edited, so readability
matters.

**Alternatives considered**:
- JSON: no comments, harder to hand-edit, but matches output format.
- YAML: implicit typing causes bugs (e.g. `NO` → `false`), extra dep.

### Decision: CLI framework → Typer

**Rationale**: Typer provides type-safe CLI definitions via type hints,
auto-generates help text, and includes Rich for table formatting (used
by the `agents` command). Single dependency covers CLI + rich output.

**Alternatives considered**:
- argparse (stdlib): verbose, no rich output, more boilerplate.
- click: Typer is built on click with less boilerplate.

### Decision: Variable interpolation → Custom regex

**Rationale**: The spec calls for `${VAR}` and `${VAR:-default}` bash-
style syntax. A simple regex (~15 lines) handles this exactly.
No dependency needed. Jinja uses different syntax (`{{ var }}`),
is a full templating engine (overkill), and adds a heavy dependency.

**Alternatives considered**:
- Jinja2: different syntax, overkill for variable substitution.
- string.Template: supports `${VAR}` but not `${VAR:-default}`.
- os.path.expandvars: env only, no defaults, no config file loading.

### Decision: Canonical config location → `~/.config/twmcp/config.toml`

**Rationale**: Follows XDG Base Directory spec. Overridable via
`--config` CLI flag. The `~/.config/` prefix is standard on macOS and
Linux for user configuration.

**Alternatives considered**:
- `~/.twmcp/config.toml`: non-standard but simpler.
- `~/.twmcp.toml`: single file in home, gets lost among dotfiles.

### Decision: Dotenv file location → `~/.config/twmcp/secrets.env`

**Rationale**: Co-located with config. Configurable via `env_file` key
in `config.toml`. Dotenv format (KEY=VALUE) is universally understood.

## Dependency Summary

| Dependency | Purpose           | Justification                     |
|------------|-------------------|------------------------------------|
| typer      | CLI + Rich output | Type-safe CLI, auto-help, tables   |
| (stdlib)   | tomllib           | TOML parsing (Python 3.11+ stdlib) |
| (stdlib)   | re                | Variable interpolation regex        |
| (stdlib)   | json              | JSON output                         |
| (stdlib)   | pathlib           | File path handling                  |
