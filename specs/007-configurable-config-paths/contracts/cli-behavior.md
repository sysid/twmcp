# Contract: CLI Behavior

## `twmcp compile <agent>` / `twmcp compile --all`

- If `[agents.<agent>] config_path = X` is set in the loaded config, the compiled JSON is written to `X` (after `~` + `${VAR}` expansion), **not** to the registry default.
- If not set, behavior is unchanged.
- `--dry-run` prints to stdout regardless of overrides. The "Written: <path>" confirmation on stderr reflects the effective path (override if present).

## `twmcp agents` (text + `--json`)

- Loads config from the default path (or `--config` flag — new, optional).
- Displays the **effective** `config_path` per agent: override if present, registry default otherwise.
- If config file is missing or unparseable: emits a single warning to stderr (`Warning: could not load config <path>: <reason>; showing built-in defaults.`) and falls back to registry. Exit 0. This preserves first-run discoverability.
- `--json` output reflects the same effective paths.

## `twmcp edit --init`

- Writes a `config.toml` to the target path. Content now includes a commented block for every registered agent:

```toml
# ---- Agent output paths (optional overrides) ----
# Uncomment and edit any block to override where twmcp writes each agent's config.
# Supports ${VAR}, ${VAR:-default}, and ~ expansion. Relative paths resolve against CWD.

# [agents.copilot-cli]
# config_path = ".copilot/mcp-config.json"

# [agents.intellij]
# config_path = "~/.config/github-copilot/intellij/mcp.json"

# [agents.claude-code]
# config_path = ".claude/mcp-config.json"

# [agents.claude-desktop]
# config_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
```

- The `~`-abbreviated paths are produced by formatting each `AGENT_REGISTRY` entry via `str(path).replace(str(Path.home()), "~")`.
- If the target file exists: existing `FileExistsError` behavior preserved — no change.

## Exit codes (unchanged, explicit for reference)

| Condition | Exit |
|---|---|
| Success | 0 |
| Config parse error (unknown agent, non-string path, unresolved `${VAR}`) | 1 |
| I/O error writing compiled output | 1 |
| `edit --init` on existing file | 1 |

## Error messages (new)

- `Error: Unknown agent "<name>" in [agents.*]. Valid agents: claude-code, claude-desktop, copilot-cli, intellij`
- `Error: [agents.<name>].config_path must be a string, got <type>`
