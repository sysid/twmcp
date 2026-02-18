# Data Model: Interactive Server Selection

**Feature**: 002-interactive-server-select
**Date**: 2026-02-18

## Entities

### Server Selection (new, transient)

A transient per-invocation set of server names. Not persisted, not part of the config data model.

```
ServerSelection:
  names: set[str]           # server names chosen by user
  source: "interactive" | "cli-argument"  # how the selection was made
```

**Lifecycle**: Created during CLI argument processing. Consumed during compilation. Discarded after process exits.

**Validation rules**:
- Every name in `names` MUST exist as a key in `CanonicalConfig.servers`
- Empty set is valid (produces informational message + clean exit)
- Names are case-sensitive, must match config keys exactly

### CanonicalConfig (existing, unchanged)

```
CanonicalConfig:
  servers: dict[str, Server]   # keyed by server name
  env_file: str | None
```

No changes to existing entities. The selection operates as a filter on `servers` keys.

## Relationships

```
┌──────────────────┐     filters     ┌──────────────────┐
│ ServerSelection   │───────────────→│ CanonicalConfig   │
│ (transient)       │                │ .servers           │
│                   │                │                    │
│ names: {"github", │                │ "github": Server   │
│  "local-proxy"}   │                │ "atlassian": Server│
│                   │                │ "local-proxy":     │
└──────────────────┘                │   Server           │
                                     └──────────────────┘
                                              │
                                     transform_for_agent
                                     (existing, unchanged)
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │ Agent JSON output │
                                     │ (only selected    │
                                     │  servers)          │
                                     └──────────────────┘
```

## State Transitions

None. Server selection is stateless — it exists only for the duration of a single CLI invocation.
