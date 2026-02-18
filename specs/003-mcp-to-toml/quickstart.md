# Quickstart: twmcp extract

## What it does

Converts an existing MCP JSON configuration file into twmcp's canonical TOML format and prints it to stdout.

## Usage

```bash
# Extract from Claude Desktop config
twmcp extract ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Extract from VS Code settings
twmcp extract ~/.config/Code/User/settings.json

# Extract from Copilot CLI config
twmcp extract ~/.copilot/mcp-config.json

# Save to a file
twmcp extract mcp-config.json > ~/.config/twmcp/config.toml
```

## Supported JSON formats

The command auto-detects these formats:

| Source | JSON structure |
|--------|---------------|
| Claude Desktop | `{"mcpServers": {...}}` |
| Copilot CLI | `{"mcpServers": {...}}` |
| VS Code | `{"mcp": {"servers": {...}}}` |
| IntelliJ | `{"servers": {...}}` |

## What happens to secrets

Environment keys ending in `_TOKEN`, `_KEY`, `_SECRET`, `_PASSWORD`, or `_CREDENTIALS` have their literal values replaced with `${VAR_NAME}` placeholders:

```
Before (JSON):  "GITHUB_TOKEN": "ghp_abc123def456"
After (TOML):   GITHUB_TOKEN = "${GITHUB_TOKEN}"
```

A header comment lists all placeholders that need environment variables set.

## What happens to unknown properties

JSON properties not recognized by twmcp are preserved as TOML comments:

```toml
[servers.my-server]
command = "my-tool"
type = "stdio"
# unknown: disabled = true
# unknown: timeout = 30
```
