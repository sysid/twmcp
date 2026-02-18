# Data Model: MCP Config Compiler

**Date**: 2026-02-17
**Branch**: `001-mcp-config-compiler`

## Entities

### CanonicalConfig

The root object parsed from `~/.config/twmcp/config.toml`.

```
CanonicalConfig
├── env_file: str | None        # path to dotenv file for variables
└── servers: dict[str, Server]  # keyed by server name
```

### Server

A single MCP server definition in the canonical config.

```
Server
├── command: str                # executable (e.g. "npx", "bash")
├── args: list[str]             # command arguments
├── type: str                   # "stdio", "http", "sse"
├── env: dict[str, str]         # environment variables (may contain ${VAR})
├── url: str | None             # for http/sse servers
├── headers: dict[str, str]     # for http servers (may contain ${VAR})
├── tools: list[str] | None     # tool filter (e.g. ["*"])
└── overrides: dict[str, PartialServer] | None  # agent-specific overrides
```

### PartialServer (Override)

A subset of Server fields that override the base definition for a
specific agent. Only fields present in the override replace the base.

```
PartialServer
├── command: str | None
├── args: list[str] | None
├── type: str | None
├── env: dict[str, str] | None
├── url: str | None
├── headers: dict[str, str] | None
└── tools: list[str] | None
```

### AgentProfile

A built-in definition of a target agent. Not user-configurable in v1.

```
AgentProfile
├── name: str                   # e.g. "copilot-cli"
├── config_path: Path           # e.g. ~/.copilot/mcp-config.json
├── top_level_key: str          # "mcpServers" or "servers"
├── type_mapping: dict[str,str] # e.g. {"stdio": "local"} for copilot
├── header_style: str           # "flat" or "nested"
└── supported_fields: set[str]  # fields this agent recognizes
```

### CompiledConfig

The output JSON for a specific agent. Ephemeral — not stored as a
model, just serialized to JSON and written to disk.

```
CompiledConfig = dict  # {top_level_key: {server_name: transformed_server}}
```

## Canonical Config Example (TOML)

```toml
env_file = "~/.config/twmcp/secrets.env"

[servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
type = "stdio"
env.GITHUB_TOKEN = "${GITHUB_TOKEN}"

[servers.github.overrides.copilot-cli]
type = "local"

[servers.atlassian]
type = "http"
url = "https://atc.bmwgroup.net/mcp/"
headers.X-Atlassian-Confluence-Personal-Token = "${CONFLUENCE_TOKEN}"
headers.X-Atlassian-Confluence-Url = "https://atc.bmwgroup.net/confluence"
headers.X-Atlassian-Jira-Personal-Token = "${JIRA_TOKEN}"
headers.X-Atlassian-Jira-Url = "https://atc.bmwgroup.net/jira"
tools = ["*"]
```

## Agent Profile Registry (built-in)

| Agent          | config_path                                      | top_level_key | type_mapping          | header_style |
|----------------|--------------------------------------------------|---------------|-----------------------|--------------|
| copilot-cli    | `~/.copilot/mcp-config.json`                     | `mcpServers`  | `stdio→local`         | flat         |
| intellij       | `~/.config/github-copilot/intellij/mcp.json`     | `servers`     | (identity)            | nested       |
| claude-desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | `mcpServers` | (omit type) | N/A    |

## Data Flow

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐
│ config.toml     │────▶│ Parse (TOML) │────▶│ CanonicalConfig│
│ (hand-edited)   │     └──────────────┘     └───────┬───────┘
└─────────────────┘                                   │
                                                      ▼
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐
│ secrets.env     │────▶│ Load dotenv  │────▶│ Variable Map   │
│ + env vars      │     └──────────────┘     └───────┬───────┘
└─────────────────┘                                   │
                                                      ▼
                                              ┌───────────────┐
                                              │ Interpolate   │
                                              │ ${VAR:-def}   │
                                              └───────┬───────┘
                                                      │
                          ┌───────────────────────────┼───────────────┐
                          ▼                           ▼               ▼
                   ┌─────────────┐           ┌──────────────┐ ┌──────────────┐
                   │ copilot-cli │           │  intellij    │ │claude-desktop│
                   │ AgentProfile│           │ AgentProfile │ │ AgentProfile │
                   └──────┬──────┘           └──────┬───────┘ └──────┬───────┘
                          ▼                          ▼                ▼
                   ┌─────────────┐           ┌──────────────┐ ┌──────────────┐
                   │ Transform   │           │  Transform   │ │  Transform   │
                   │ + Write JSON│           │ + Write JSON │ │ + Write JSON │
                   └─────────────┘           └──────────────┘ └──────────────┘
```

## Validation Rules

- Server `command` is required for stdio servers, forbidden for http/sse.
- Server `url` is required for http/sse servers, forbidden for stdio.
- Server `type` MUST be one of: `stdio`, `http`, `sse`.
- Override keys MUST match registered agent names (warn on unknown).
- Variable references MUST resolve or have defaults (fail otherwise).
- `env_file` path MUST exist if specified (fail otherwise).
