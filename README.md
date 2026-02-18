# twmcp

One canonical TOML config for all your MCP servers. Compiled to agent-specific JSON.

## The Problem

AI coding agents (GitHub Copilot CLI, IntelliJ Copilot, Claude Desktop) each need MCP server
configurations in their own format — different JSON keys, different type names, different header
structures, different file locations. Maintaining these configs separately means:

- Duplicate definitions across 3+ JSON files
- Secrets scattered in multiple locations
- Agent-specific quirks handled manually (e.g., Claude Desktop silently ignores HTTP servers)
- Adding a server means editing every agent config

## The Solution

Define your MCP servers once in TOML. `twmcp` compiles agent-specific JSON to each agent's
expected location, handling type mappings, header formats, server compatibility, and secret
injection.

```
config.toml ──→ twmcp compile ──→ ~/.copilot/mcp-config.json            (Copilot CLI)
                                  ~/.config/github-copilot/.../mcp.json  (IntelliJ)
                                  ~/Library/.../claude_desktop_config.json(Claude Desktop)
```

## Installation

Requires Python 3.13+.

```bash
pip install twmcp
# or
uv pip install twmcp
```

## Quick Start

### 1. Create a canonical config

```bash
mkdir -p ~/.config/twmcp
```

`~/.config/twmcp/config.toml`:

```toml
env_file = "secrets.env"   # relative to config directory

[servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
type = "stdio"

[servers.github.env]
GITHUB_TOKEN = "${GITHUB_TOKEN}"

[servers.github.overrides.copilot-cli]
type = "local"             # Copilot CLI calls stdio servers "local"

[servers.atlassian]
type = "http"
url = "https://mycompany.atlassian.net/mcp/"
tools = ["*"]

[servers.atlassian.headers]
Authorization = "Bearer ${CONFLUENCE_TOKEN}"

[servers.local-proxy]
command = "mcp-proxy"
args = ["http://localhost:8113/sse"]
type = "stdio"

[servers.local-proxy.env]
API_TOKEN = "${API_TOKEN:-default-token}"
```

### 2. Add your secrets

`~/.config/twmcp/secrets.env`:

```env
GITHUB_TOKEN=ghp_abc123
CONFLUENCE_TOKEN=my-confluence-token
```

Environment variables override dotenv values.

### 3. Compile

```bash
# Compile for a single agent
twmcp compile copilot-cli

# Compile for all agents
twmcp compile --all

# Preview without writing files
twmcp compile copilot-cli --dry-run

# Select specific servers interactively
twmcp compile copilot-cli --select

# Filter servers non-interactively
twmcp compile --all --select github,local-proxy
```

## What Gets Generated

From the config above, each agent receives a tailored JSON file:

### Copilot CLI (`~/.copilot/mcp-config.json`)

```json
{
  "mcpServers": {
    "github": {
      "type": "local",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_abc123" }
    },
    "atlassian": {
      "type": "http",
      "url": "https://mycompany.atlassian.net/mcp/",
      "headers": { "Authorization": "Bearer my-confluence-token" },
      "tools": ["*"]
    },
    "local-proxy": {
      "type": "local",
      "command": "mcp-proxy",
      "args": ["http://localhost:8113/sse"],
      "env": { "API_TOKEN": "default-token" }
    }
  }
}
```

### IntelliJ (`~/.config/github-copilot/intellij/mcp.json`)

```json
{
  "servers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_abc123" }
    },
    "atlassian": {
      "type": "http",
      "url": "https://mycompany.atlassian.net/mcp/",
      "requestInit": {
        "headers": { "Authorization": "Bearer my-confluence-token" }
      },
      "tools": ["*"]
    }
  }
}
```

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_abc123" }
    },
    "local-proxy": {
      "command": "mcp-proxy",
      "args": ["http://localhost:8113/sse"],
      "env": { "API_TOKEN": "default-token" }
    }
  }
}
```

Claude Desktop only supports stdio servers — HTTP servers like `atlassian` are
automatically skipped. The `type` field is also omitted since Claude Desktop doesn't use it.

## Agent Differences

| Aspect         | Copilot CLI        | IntelliJ               | Claude Desktop         |
|----------------|--------------------|------------------------|------------------------|
| Top-level key  | `mcpServers`       | `servers`              | `mcpServers`           |
| Type mapping   | `stdio` → `local`  | (none)                 | (none)                 |
| Headers        | flat               | nested in `requestInit`| n/a                    |
| HTTP servers   | supported          | supported              | skipped                |
| `type` field   | included           | included               | omitted                |

## Config Reference

### Top-level

| Key        | Type   | Required | Description                              |
|------------|--------|----------|------------------------------------------|
| `env_file` | string | no       | Path to dotenv file (relative to config) |

### Server Definition (`[servers.<name>]`)

| Key         | Type     | Required     | Description                    |
|-------------|----------|--------------|--------------------------------|
| `type`      | string   | yes          | `stdio`, `http`, or `sse`      |
| `command`   | string   | for stdio    | Executable command             |
| `args`      | string[] | no           | Command arguments              |
| `url`       | string   | for http/sse | Server URL                     |
| `env`       | table    | no           | Environment variables          |
| `headers`   | table    | no           | HTTP headers                   |
| `tools`     | string[] | no           | Tool filter                    |
| `overrides` | table    | no           | Agent-specific field overrides |

### Variable Interpolation

Values support `${VAR}` and `${VAR:-default}` syntax:

```
${GITHUB_TOKEN}              # resolved from env or dotenv — error if missing
${API_TOKEN:-default-token}  # uses default if not found anywhere
```

Resolution priority: **environment variable > dotenv file > default value**.

All unresolved variables (no value, no default) are reported together in a single error
message.

### Agent-Specific Overrides (`[servers.<name>.overrides.<agent>]`)

Override any server field for a specific agent. Only non-null fields are applied:

```toml
[servers.github.overrides.copilot-cli]
type = "local"    # override type for copilot-cli only
```

## CLI Reference

```
twmcp compile <agent>               # compile for one agent
twmcp compile --all                 # compile for all agents
twmcp compile <agent> --dry-run     # preview JSON output
twmcp compile <agent> --select      # interactive server picker
twmcp compile <agent> --select a,b  # filter to named servers
twmcp compile --all --select a,b    # filter applied to all agents
twmcp compile <agent> --config PATH # use custom config path

twmcp agents                        # list supported agents
twmcp agents --json                 # list as JSON
```

### `--select` Flag

The `--select` flag operates in two modes:

- **Bare** (`--select`): Opens an interactive terminal prompt where you toggle servers
  with Space and confirm with Enter. All servers are pre-selected (opt-out model).
- **With value** (`--select github,local-proxy`): Filters to the named servers without
  any interactive prompt. Unknown names produce an error listing available servers.

When used with `--all`, the selection is applied once and used for all agent compilations.

## Architecture

```
config.toml + secrets.env
        │
        ▼
┌─────────────────┐     ┌──────────────────┐
│ config.py       │────▶│ interpolate.py   │
│ TOML parsing    │     │ ${VAR} resolver  │
│ dataclasses     │     │ dotenv loader    │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ cli.py          │────▶│ selector.py      │
│ compile command │     │ --select logic   │
│ agents command  │     │ interactive menu │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ compiler.py     │────▶│ agents.py        │
│ transform logic │     │ profile registry │
│ JSON writer     │     │ per-agent config │
└─────────────────┘     └──────────────────┘
```

The transformation pipeline per server:

1. Apply agent-specific overrides (merge `PartialServer` onto `Server`)
2. Map type names (`stdio` → `local` for Copilot CLI)
3. Skip incompatible servers (HTTP on Claude Desktop)
4. Format headers per agent style (flat / nested in `requestInit`)
5. Omit empty fields and agent-irrelevant fields
6. Wrap in agent's top-level key and write JSON

## Development

```bash
make test       # run tests with coverage
make format     # ruff formatting
make lint       # ruff check --fix
make build      # format + build
```


### Typer/Click Monkey-Patching
- Typer recreates Click commands on every `get_command()` call - one-time patches get lost
- `typer.testing.CliRunner` imports `get_command` at module level as `_get_command` - patching `typer.main.get_command` alone doesn't affect tests
- Must patch BOTH `typer.main.get_command` AND `typer.testing._get_command`
- Use `from typer import testing as _tt` (not `import typer.testing`) inside functions to avoid Python scoping issues with the `typer` name

### Architecture
- `selector.py` - server selection utilities (parse, validate, interactive prompt)
- `cli.py` - typer app with `compile` and `agents` commands
- `_resolve_selection()` in cli.py handles both interactive and non-interactive `--select`
- Click `_flag_needs_value` patch enables dual-mode `--select` (bare=interactive, with value=filter)

## License

BSD-3-Clause
