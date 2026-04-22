# Contract: TOML Config Schema — `[agents.*]` Section

## Schema

```toml
# Existing keys (unchanged):
# env_file = "secrets.env"
# [servers.<name>] ...

# NEW — all fields optional, whole section optional:
[agents.<agent-name>]
config_path = "<path string>"   # required within the section if the section exists
```

**`<agent-name>`**: must be one of the registered agents: `copilot-cli`, `intellij`, `claude-code`, `claude-desktop` (and any future registry additions).

**`<path string>`**:
- May contain `${VAR}` or `${VAR:-default}` placeholders (resolved via existing interpolation).
- May start with `~` or `~user` (expanded to home directory).
- May be absolute or relative. Relative paths resolve against current working directory at write time.

## Validation rules

| Rule | Error message (exit 1) |
|---|---|
| Unknown agent name in `[agents.<name>]` | `Unknown agent "<name>" in [agents.*]. Valid agents: <sorted csv>` |
| `config_path` is not a string | `[agents.<name>].config_path must be a string, got <type>` |
| `${VAR}` placeholder has no value | Existing message: `Unresolved variables: <list>` (unchanged — inherited from `_collect_unresolved`) |
| Section `[agents]` absent | No error. Built-in defaults apply. |
| Section `[agents.<name>]` present but empty | No error. Built-in default applies to `<name>`. (`config_path` key just absent.) |

## Example

```toml
env_file = "secrets.env"

[agents.claude-code]
config_path = "${PROJECT_ROOT}/.mcp/claude.json"

[agents.claude-desktop]
config_path = "~/dotfiles/claude/desktop.json"

[servers.foo]
command = "npx"
args = ["-y", "foo-mcp"]
```

## Backwards compatibility

Any existing valid `config.toml` (without `[agents.*]`) remains valid and produces identical behavior.
