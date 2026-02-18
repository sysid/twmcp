# CLI Contract: `--select` Flag

**Feature**: 002-interactive-server-select
**Date**: 2026-02-18

## Command Signature

```
twmcp compile [AGENT] [--all] [--config PATH] [--dry-run] [--select [VALUE]]
```

## `--select` Behavior Matrix

| Invocation | `select` value | Mode | TTY required | Behavior |
|-----------|---------------|------|-------------|----------|
| `twmcp compile copilot-cli` | `None` | Default | No | All servers compiled (existing behavior) |
| `twmcp compile copilot-cli --select` | `"__interactive__"` | Interactive | **Yes** | Multi-select prompt shown, compile selected |
| `twmcp compile copilot-cli --select github,local-proxy` | `"github,local-proxy"` | Filter | No | Parse names, validate, compile subset |
| `twmcp compile --all --select` | `"__interactive__"` | Interactive | **Yes** | Prompt once, apply to all agents |
| `twmcp compile --all --select github` | `"github"` | Filter | No | Filter applied to all agents |

## Exit Codes

| Scenario | Exit Code | Stderr Output |
|----------|-----------|---------------|
| Success (servers compiled) | 0 | `Written: <path>` per file |
| User cancelled (Ctrl+C / Escape) | 0 | (none) |
| No servers selected (interactive) | 0 | `No servers selected.` |
| Unknown server name in `--select <value>` | 1 | `Error: Unknown server(s): "x"\n  Available: a, b, c` |
| `--select` bare on non-TTY stdin | 1 | `Error: --select requires an interactive terminal. Use --select <names> for non-interactive mode.` |
| `--select` with empty string | 1 | `Error: No server names provided to --select.` |

## Interactive Prompt Format

```
Select MCP servers (Space=toggle, Enter=confirm, Esc=cancel):
  [x] github [stdio]
  [x] atlassian [http]
  [x] local-proxy [stdio]
```

- All entries pre-selected by default (opt-out model)
- Display format: `<name> [<type>]`
- Items ordered as they appear in the TOML config

## Non-Interactive Filter Parsing

```
--select github,local-proxy
```

- Comma-separated, no spaces around commas
- Names validated against `CanonicalConfig.servers` keys
- Fail-fast on any unrecognized name (no partial output)
