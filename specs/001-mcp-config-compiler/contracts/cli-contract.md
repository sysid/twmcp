# CLI Contract: twmcp

**Date**: 2026-02-17

## Commands

### `twmcp compile <agent>`

Compile canonical config for a specific agent and write to the agent's
config file location.

```
twmcp compile <agent> [--config PATH] [--dry-run]

Arguments:
  agent           Agent name (e.g. copilot-cli, intellij, claude-desktop)

Options:
  --config PATH   Path to canonical config [default: ~/.config/twmcp/config.toml]
  --dry-run       Print compiled JSON to stdout, do not write files

Exit codes:
  0   Success
  1   Error (unknown agent, parse error, unresolved variables, I/O error)

stdout: (dry-run only) compiled JSON
stderr: warnings (skipped fields), errors
```

### `twmcp compile --all`

Compile canonical config for ALL registered agents.

```
twmcp compile --all [--config PATH] [--dry-run]

Options:
  --config PATH   Path to canonical config [default: ~/.config/twmcp/config.toml]
  --dry-run       Print all compiled configs to stdout (agent-name-headed)

Exit codes:
  0   Success (all agents compiled)
  1   Error (any agent fails)

stdout: (dry-run only) compiled JSON per agent, separated by headers
stderr: warnings, errors, per-agent status
```

### `twmcp agents`

List all supported agents with config details.

```
twmcp agents [--json]

Options:
  --json          Output as JSON array instead of table

Exit codes:
  0   Always (informational command)

stdout:
  (default) Rich table:
    Agent           Config Path                          Key
    copilot-cli     ~/.copilot/mcp-config.json           mcpServers
    intellij        ~/.config/github-copilot/.../mcp.json servers
    claude-desktop  ~/Library/.../claude_desktop_config.json mcpServers

  (--json) JSON array:
    [
      {"name": "copilot-cli", "config_path": "...", "top_level_key": "mcpServers"},
      ...
    ]
```

## Error Message Format

All errors follow the pattern:

```
Error: <what failed>
  <context details>
  <actionable suggestion>
```

Examples:

```
Error: Unknown agent "foo"
  Available agents: copilot-cli, intellij, claude-desktop
  Run 'twmcp agents' to see all supported agents.
```

```
Error: Unresolved variables in config
  ${GITHUB_TOKEN} - not set, no default
  ${LINEAR_API_KEY} - not set, no default
  Set these environment variables or add defaults: ${VAR:-default}
```

```
Error: Config file not found
  Expected: ~/.config/twmcp/config.toml
  Create the file or use --config to specify a different path.
```
