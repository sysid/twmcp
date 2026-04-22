# Phase 1 Data Model

## Modified: `CanonicalConfig`

Existing dataclass in `src/twmcp/config.py`. One additive field:

```python
@dataclass
class CanonicalConfig:
    servers: dict[str, Server]
    env_file: str | None = None
    agent_overrides: dict[str, str] = field(default_factory=dict)  # NEW
```

| Field | Type | Required | Description |
|---|---|---|---|
| `servers` | `dict[str, Server]` | yes | existing |
| `env_file` | `str \| None` | no | existing |
| `agent_overrides` | `dict[str, str]` | no (default `{}`) | Maps registered agent name → override `config_path` string (post-interpolation, pre-`expanduser`). Empty dict when `[agents]` absent. |

**Validation rules** (enforced in `_parse_raw` or new `_parse_agent_overrides`):

1. Every key in `agent_overrides` MUST be a member of `AGENT_REGISTRY`. Otherwise: `ValueError: Unknown agent "<name>" in [agents.*]. Valid agents: <sorted list>`.
2. Every `config_path` value MUST be a `str` after TOML parsing. Otherwise: `ValueError: [agents.<name>].config_path must be a string, got <type>`.
3. Unknown keys inside `[agents.<name>]` (e.g. `[agents.claude-code] typo = "..."`) are **ignored** for forward compatibility. (Not a user-facing gotcha today; revisit if abuse emerges.)

## Unchanged: `AgentProfile`

Stays `frozen=True` in `src/twmcp/agents.py`. No structural change.

## New helper: `resolve_profile(name, overrides)` → `AgentProfile`

Signature (in `src/twmcp/agents.py`):

```python
def resolve_profile(name: str, overrides: dict[str, str]) -> AgentProfile:
    """Return the profile for `name` with its config_path replaced by the override, if any.

    Applies Path.expanduser() to the override string.
    Raises KeyError for unknown agents (delegates to get_profile).
    """
```

Pure function. Returns a new `AgentProfile` instance when an override exists; returns the registry entry unchanged otherwise.

## State transitions

None. This is a stateless, load-time transformation.

## Relationships

```
config.toml
  └── [agents.<name>]           ──validated-against──>   AGENT_REGISTRY (keys)
        └── config_path:str     ──interpolated-by──>     _resolve_value  (${VAR}, ${VAR:-default})
                                ──expanded-by──>         Path.expanduser (~)
                                ──merged-into──>         resolved AgentProfile per invocation
                                ──consumed-by──>         compile, compile --all, agents
```

## Invariants

- `AGENT_REGISTRY` is never mutated.
- `CanonicalConfig.agent_overrides` contains only validated, registered agent names.
- Effective `config_path` returned by `resolve_profile` is a `pathlib.Path` with `~` already expanded (may still be relative — resolves at I/O time against CWD, matching existing default behavior).
