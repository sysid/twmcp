# Quickstart: Overriding Agent Output Paths

## 1. Create (or open) your config

```bash
twmcp edit --init          # first time only
twmcp edit                 # subsequent edits
```

The generated file contains a commented block at the bottom listing every supported agent with its built-in default.

## 2. Uncomment and edit the agent(s) you want to redirect

```toml
[agents.claude-code]
config_path = "${PROJECT_ROOT}/.mcp/claude.json"

[agents.claude-desktop]
config_path = "~/dotfiles/claude/desktop.json"
```

Supported expansions:
- `~` → home directory
- `${VAR}` / `${VAR:-default}` → environment variable (with optional default)
- Relative paths → resolved against your current working directory

## 3. Verify the effective paths

```bash
twmcp agents
```

```
Agent                Config Path                                        Key
-------------------- -------------------------------------------------- ---------------
copilot-cli          .copilot/mcp-config.json                           mcpServers
intellij             ~/.config/github-copilot/intellij/mcp.json         servers
claude-code          /Users/you/work/myproject/.mcp/claude.json         mcpServers    ← override
claude-desktop       ~/dotfiles/claude/desktop.json                     mcpServers    ← override
```

## 4. Compile

```bash
twmcp compile claude-code
# Written: /Users/you/work/myproject/.mcp/claude.json
```

## Errors you might hit

| Symptom | Cause | Fix |
|---|---|---|
| `Error: Unknown agent "claude-5" in [agents.*]. Valid agents: ...` | Typo or agent not in registry | Use a valid agent name |
| `Error: [agents.foo].config_path must be a string, got <class 'dict'>` | Wrote a table instead of a string | `config_path = "..."` |
| `Error: Unresolved variables: PROJECT_ROOT` | `${PROJECT_ROOT}` not set | `export PROJECT_ROOT=...` or use `${PROJECT_ROOT:-./}` |

## Leaving things unchanged

Remove or comment out the `[agents.<name>]` block to fall back to the built-in default for that agent. Removing the entire `[agents]` section restores full default behavior.
