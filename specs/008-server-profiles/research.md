# Phase 0 Research: Named Server Profiles

No `NEEDS CLARIFICATION` markers in plan or spec — Q1/Q2 in
`/speckit.clarify` resolved the only open scope decisions. Research is
limited to validating the chosen design against the existing codebase.

## Decision 1: TOML schema location for profiles

**Decision**: Top-level `[profiles]` table — keys are profile names,
values are arrays of server-name strings.

```toml
[profiles]
emea = ["aws-mcp-e2e-losnext-emea", "aws-mcp-e2e-los-emea"]
apac = ["aws-mcp-e2e-apac-1"]
```

**Rationale**: Mirrors the existing `[servers]` and `[agents.*]`
conventions — every authored construct lives in the canonical TOML, top
level. `tomllib` parses this natively. No schema file or external
validator needed.

**Alternatives considered**:
- Nested under `[servers]` (e.g. `[servers.profiles.emea]`) — rejected:
  conflates server definitions with named groupings.
- Separate `profiles.toml` file — rejected: violates "one canonical
  config" principle and adds a new path-resolution rule.

## Decision 2: Profile resolution placement

**Decision**: Add `_resolve_profile` helper in `selector.py` (alongside
`parse_select_value`, `validate_server_names`). Wire it into the existing
`_resolve_selection` in `cli.py` as a third routing branch
(profile / interactive / select / none).

**Rationale**: `_resolve_selection` already routes between
`--interactive` and `--select`; adding `--profile` is a parallel branch
with identical output (a filtered `CanonicalConfig`). Keeps the routing
logic linear and avoids growing a new module.

**Alternatives considered**:
- Resolve at config-load time (turn `[profiles]` into pre-filtered
  configs) — rejected: forces config to know about CLI args and breaks
  the `agents` and `extract` commands which don't take a profile.
- Separate `ProfileResolver` class — rejected as premature abstraction
  for a single function (≤ 30 LOC).

## Decision 3: `profiles` command shape

**Decision**: New `twmcp profiles` command, mirroring `twmcp agents`:

- `twmcp profiles` — table output: profile name + member servers
- `twmcp profiles --json` — JSON array of `{name, servers}` objects
- `--config <path>` — same flag as other commands

**Rationale**: User Story 2 maps 1:1 to the existing `agents` command
shape. Reuse the same flag conventions (`--json`, `--config`) so users
have one mental model.

## Decision 4: Interactive pre-seeding (P3)

**Decision**: Use `simple-term-menu`'s `preselected_entries` parameter
when `--profile` and `--interactive` are combined.

**Rationale**: `simple-term-menu` (already a project dependency, used in
`select_servers_interactive`) accepts preselected indices. Confirmed via
the library's API. No new dependency.

**Alternatives considered**:
- Skip pre-seeding, just filter to profile's servers — rejected:
  defeats the purpose of combining the flags.

## Decision 5: Validation timing for `[profiles]`

**Decision**: Validate profile *structure* (types, non-empty profile
names) at config load time in `_parse_profiles`. Validate that profile
*server references* exist in `[servers]` at compile time, when the user
actually selects a profile via `--profile`.

**Rationale**: Structural errors (non-string entries, non-list values)
are config-author bugs and should fail load fast. Reference errors
(profile names a server that doesn't exist) only matter when the user
selects that profile — a stale profile referencing an old server name
should not break `twmcp agents` or `twmcp compile <agent>` without
`--profile`. This matches FR-008 (no behavior change without `--profile`).

**Alternatives considered**:
- Validate references at load time too — rejected: makes a stale profile
  break unrelated commands.

## Decision 6: `extract` command unchanged

**Decision**: `extract` (JSON → TOML) does not emit `[profiles]`.

**Rationale**: Profiles are an authored construct that doesn't exist in
compiled agent JSON. Round-tripping through `extract` produces a
profile-less canonical config, which is correct — the user can re-add
profiles by hand if desired. Per spec assumption.
