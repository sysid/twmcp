# CLI Contract: Named Server Profiles

## `compile` command — new flag

```
twmcp compile <agent> [--all] [--config <path>] [--dry-run]
                      [--select <names>] [--interactive]
                      [--profile <name>]                    ← NEW
```

| Invocation | Behavior | Exit |
|---|---|---|
| `compile <agent>` (no profile) | All servers compiled. **Unchanged from today.** | 0 |
| `compile <agent> --profile emea` | Only servers in profile `emea` compiled. | 0 |
| `compile --all --profile emea` | Profile `emea` applied uniformly to every agent. | 0 (unless any agent write fails) |
| `compile <agent> --profile emea --select s1` | Error: `--profile` and `--select` are mutually exclusive. | 1 |
| `compile <agent> --profile emea --interactive` | Interactive menu opens with profile's servers preselected. User confirms/refines. | 0 (or 0 on cancel) |
| `compile <agent> --profile nope` (no `[profiles]` section) | Error: `No profiles defined in <config>. Add a [profiles] table.` | 1 |
| `compile <agent> --profile nope` (`[profiles]` exists, no key `nope`) | Error: `Unknown profile "nope". Available: emea, apac` | 1 |
| `compile <agent> --profile bad` (profile references missing server) | Error: `Profile "bad" references unknown server(s): server-x, server-y` | 1 |
| `compile <agent> --profile empty` (`empty = []`) | Empty compiled output written; same as `--select none`. | 0 |

## `profiles` command — new

```
twmcp profiles [--config <path>] [--json]
```

| Invocation | Output | Exit |
|---|---|---|
| `profiles` (with profiles defined) | Table: profile name + comma-joined server list. | 0 |
| `profiles --json` (with profiles defined) | JSON array: `[{"name": "emea", "servers": ["s1", "s2"]}, ...]` | 0 |
| `profiles` (no `[profiles]` section) | Message: `No profiles defined in <config>.` to stderr. | 0 |
| `profiles --json` (no `[profiles]` section) | Empty array `[]` to stdout. | 0 |
| `profiles` (config not found) | Same warning behavior as `agents` command (warn, show defaults — but defaults are empty for profiles). | 0 |

## Error message format

All errors follow the project's existing convention:
- Prefix with `Error: ` to stderr
- Single-line summary, optional indented hint on subsequent line(s)
- Exit code 1

Example:
```
Error: Unknown profile "nope".
  Available profiles: apac, emea
  Run 'twmcp profiles' to see all defined profiles.
```

## Debug logging (`-v`)

Required log lines (per FR-010):

```
DEBUG  --profile=<name> requested
DEBUG  profile <name>: resolved to N server(s): [<sorted list>]
DEBUG  profile <name>: excluded M server(s) not in profile: [<sorted list>]
```

Existing `_resolve_selection` debug lines are preserved.

## Mutual exclusion summary

```
                      ┌─────────────┬─────────────┬──────────────┐
                      │ --select    │ --interactive│ --profile    │
┌─────────────────────┼─────────────┼─────────────┼──────────────┤
│ --select            │     —       │  exclusive  │  exclusive   │
│ --interactive       │  exclusive  │     —       │  COMBINABLE  │
│ --profile           │  exclusive  │  COMBINABLE │      —       │
└─────────────────────┴─────────────┴─────────────┴──────────────┘
```

Only `--profile` + `--interactive` is combinable; that combination
pre-seeds the picker.
