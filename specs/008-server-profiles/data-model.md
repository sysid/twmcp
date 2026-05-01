# Phase 1 Data Model: Named Server Profiles

## TOML schema delta

```toml
# Existing — unchanged
[servers]
[servers.<name>]
command = "..."
args = [...]
type = "stdio" | "http" | "sse"
env = { ... }
url = "..."
headers = { ... }
tools = [...]
[servers.<name>.overrides.<agent-name>]
# ... per-agent overrides

# Existing — unchanged
[agents.<agent-name>]
config_path = "..."

# NEW
[profiles]
<profile-name> = ["<server-name>", ...]
```

## CanonicalConfig delta

`config.py:CanonicalConfig` gains one optional field:

```python
@dataclass
class CanonicalConfig:
    servers: dict[str, Server]
    env_file: str | None = None
    agent_overrides: dict[str, str] = field(default_factory=dict)
    profiles: dict[str, list[str]] = field(default_factory=dict)   # NEW
```

`profiles` defaults to an empty dict for configs that don't define
`[profiles]` — guaranteeing FR-008 (no behavior change without
`--profile`).

## Validation rules

| Rule | Where | Failure mode |
|---|---|---|
| `[profiles]` must be a TOML table | `_parse_profiles` (config load) | `ValueError: [profiles] must be a table, got <type>` |
| Each profile value must be a list | `_parse_profiles` (config load) | `ValueError: [profiles].<name> must be a list of server names, got <type>` |
| Each list entry must be a string | `_parse_profiles` (config load) | `ValueError: [profiles].<name>[<i>] must be a string, got <type>` |
| Profile names must be non-empty strings | `_parse_profiles` (config load) | `ValueError: profile name must be a non-empty string` |
| `--profile <name>` exists in `[profiles]` | `selector._resolve_profile` (compile time) | `ValueError: Unknown profile "<name>". Available: <list> (or "(none defined)")` |
| Each referenced server exists in `[servers]` | `selector._resolve_profile` (compile time) | `ValueError: Profile "<name>" references unknown server(s): <list>` |
| `--profile` exclusive with `--select` | `cli._resolve_selection` | Exit 1, "Error: --profile and --select are mutually exclusive" |

Empty profile list (`emea = []`) is **valid** — produces an empty
compiled output, same as `--select none`. Documented edge case.

Duplicate server names within a profile are **deduplicated silently**
(set semantics for filtering). Documented edge case.

## Entity: Profile

| Attribute | Type | Notes |
|---|---|---|
| `name` | `str` | TOML key. Non-empty. |
| `servers` | `list[str]` | Server names referenced from `[servers]`. |

No identity beyond name. No state transitions. No persistence beyond the
canonical TOML file.

## Profile resolution flow

```
compile <agent> --profile <name>
        │
        ▼
load_and_resolve(config_path)              ← parses [profiles]; validates structure only
        │
        ▼
_resolve_selection(select=None,
                   interactive=False,
                   profile=<name>)
        │
        ▼
_resolve_profile(name, canonical)          ← validates name exists; validates server refs
        │
        ▼
filtered CanonicalConfig                   ← same shape as today's --select path
        │
        ▼
transform_for_agent + write_config         ← unchanged; warn-and-skip behavior preserved
```

When `--profile <name> --interactive` is combined, the picker is opened
with the profile's servers as preselected entries; user confirms or
refines. Output of the picker becomes the filtered set.
