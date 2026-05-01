# Quickstart: Named Server Profiles

## Author a profile

Edit your canonical config (default: `~/.config/twmcp/config.toml`) and
add a `[profiles]` section. Each profile is a name → list of server
names already defined under `[servers]`.

```toml
[servers.aws-mcp-e2e-losnext-emea]
command = "npx"
args = ["-y", "@aws/mcp-server"]

[servers.aws-mcp-e2e-los-emea]
command = "npx"
args = ["-y", "@aws/mcp-server"]

[servers.aws-mcp-e2e-apac]
command = "npx"
args = ["-y", "@aws/mcp-server"]

[profiles]
emea = ["aws-mcp-e2e-losnext-emea", "aws-mcp-e2e-los-emea"]
apac = ["aws-mcp-e2e-apac"]
```

## Compile only the profile's servers

```bash
twmcp compile claude-code --profile emea
# Written: .mcp.json    (containing only the two emea servers)
```

For all agents at once:

```bash
twmcp compile --all --profile emea
```

## List defined profiles

```bash
twmcp profiles
# Profile      Servers
# ------------ -----------------------------------------------------------
# emea         aws-mcp-e2e-losnext-emea, aws-mcp-e2e-los-emea
# apac         aws-mcp-e2e-apac
```

Or as JSON:

```bash
twmcp profiles --json
# [
#   {"name": "apac", "servers": ["aws-mcp-e2e-apac"]},
#   {"name": "emea", "servers": ["aws-mcp-e2e-losnext-emea", "aws-mcp-e2e-los-emea"]}
# ]
```

## Refine a profile interactively on a one-off basis

```bash
twmcp compile claude-code --profile emea --interactive
# Opens a terminal menu with the two emea servers pre-selected.
# Toggle off the ones you don't want; press Enter to compile the result.
```

## Behavior without `--profile`

Unchanged: every server in `[servers]` is compiled. Adding a `[profiles]`
section does not change the default behavior of any existing command.

## Errors you might see

| Error | Cause | Fix |
|---|---|---|
| `Unknown profile "X". Available: ...` | `--profile X` named a profile not in `[profiles]`. | Use one of the listed names, or add `X` to `[profiles]`. |
| `Profile "X" references unknown server(s): ...` | Profile lists a server not in `[servers]`. | Fix the typo in the profile or define the server. |
| `--profile and --select are mutually exclusive` | Both flags passed. | Choose one. |
| `No profiles defined in <config>` | `--profile` used but `[profiles]` is missing. | Add a `[profiles]` table to the config. |

## Debugging

Run with `-v` to see profile resolution decisions:

```bash
twmcp -v compile claude-code --profile emea
# DEBUG  --profile='emea' requested
# DEBUG  profile 'emea': resolved to 2 server(s): ['aws-mcp-e2e-los-emea', 'aws-mcp-e2e-losnext-emea']
# DEBUG  profile 'emea': excluded 1 server(s) not in profile: ['aws-mcp-e2e-apac']
```
