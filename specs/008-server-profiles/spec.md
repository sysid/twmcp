# Feature Specification: Named Server Profiles

**Feature Branch**: `008-server-profiles`
**Created**: 2026-05-01
**Status**: Draft
**Input**: User description: "I want to have the capability of collection mcp configurations into named profiles, e.g. \"aws-mcp-e2e-losnext-emea, aws-mcp-e2e-los-emea\" into the profile \"emea\"."

## Clarifications

### Session 2026-05-01

- Q: Should the config support a default profile that applies when `--profile` is omitted? → A: No default profile — `--profile` is always explicit; omitting it compiles all servers (FR-008 unchanged).
- Q: How should the compiler treat profile-selected servers that an agent can't represent (e.g., http server compiled for claude-desktop)? → A: Keep current warn-and-skip behavior; same treatment whether or not the server was profile-selected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compile a Predefined Profile (Priority: P1)

A user maintains a single canonical config that contains many MCP servers
(dozens, across regions, environments, and concerns). Today, to compile a
working subset they must either edit the config or pass `--select
aws-mcp-e2e-losnext-emea,aws-mcp-e2e-los-emea,...` every time. Instead, they
want to declare a **profile** named `emea` once in the config that lists those
two servers, and then run `twmcp compile <agent> --profile emea` whenever they
need that subset.

**Why this priority**: This is the core value of the feature. Without it,
users with many servers must repeat long server-name lists on the command
line, copy/paste them into shell aliases, or maintain multiple parallel
config files — which is exactly the duplication this tool was built to
eliminate.

**Independent Test**: Can be fully tested by adding a `[profiles]` section to
a fixture config that defines `emea = ["aws-mcp-e2e-losnext-emea",
"aws-mcp-e2e-los-emea"]`, running `twmcp compile copilot-cli --profile emea
--dry-run`, and verifying the output JSON contains exactly those two servers
under `mcpServers`.

**Acceptance Scenarios**:

1. **Given** a config with `[profiles] emea = ["server-a", "server-b"]` and a
   `[servers]` section that contains `server-a`, `server-b`, and `server-c`,
   **When** the user runs `twmcp compile <agent> --profile emea`, **Then**
   the compiled output contains only `server-a` and `server-b`.
2. **Given** a config with profile `emea` defined, **When** the user runs
   `twmcp compile <agent>` without `--profile`, **Then** all servers are
   compiled (existing default behavior is preserved).
3. **Given** a config with no `[profiles]` section, **When** the user runs
   `twmcp compile <agent> --profile anything`, **Then** the command fails
   with a clear message that no profiles are defined.
4. **Given** a config with profile `emea`, **When** the user runs `twmcp
   compile <agent> --profile nonexistent`, **Then** the command fails with a
   clear message listing the available profile names.
5. **Given** a profile that references a server name not present in
   `[servers]`, **When** the user compiles with that profile, **Then** the
   command fails with a clear message naming the missing server(s).

---

### User Story 2 - Discover Available Profiles (Priority: P2)

A user picks up a teammate's config or returns to their own after a few
weeks. Before compiling, they want to see which profiles are defined and
which servers each profile contains, without opening the TOML file.

**Why this priority**: Without discoverability, profiles become tribal
knowledge — users forget which profiles exist or which servers they
include, and fall back to manual `--select` lists, defeating the feature.
Important but not blocking — the user can always grep the config.

**Independent Test**: Can be fully tested by adding profiles to a fixture
config and running `twmcp profiles --config <fixture>`, verifying each
profile name and its server list appear in the output, and that `--json`
emits a parseable JSON array.

**Acceptance Scenarios**:

1. **Given** a config with two profiles `emea` and `apac`, **When** the user
   runs `twmcp profiles`, **Then** both profile names appear with their
   member server names.
2. **Given** a config with no `[profiles]` section, **When** the user runs
   `twmcp profiles`, **Then** the command exits successfully with a message
   indicating no profiles are defined.
3. **Given** a config with profiles, **When** the user runs `twmcp profiles
   --json`, **Then** the output is a valid JSON array of objects, each with
   a profile name and its server list.

---

### User Story 3 - Combine a Profile with Interactive or Manual Selection (Priority: P3)

A user wants to compile the `emea` profile but exclude one server from it
on this run, or wants to start the interactive picker pre-seeded with the
profile's servers.

**Why this priority**: Refinement on top of P1. Useful, but rare in
practice — most users will define the profile they actually want.

**Independent Test**: Run `twmcp compile <agent> --profile emea --interactive`
and verify the interactive menu opens with the profile's servers
pre-selected. Run `twmcp compile <agent> --profile emea --select server-a`
and verify it fails (mutually exclusive) with a clear message.

**Acceptance Scenarios**:

1. **Given** a config with profile `emea`, **When** the user runs `twmcp
   compile <agent> --profile emea --select server-x`, **Then** the command
   fails with a clear message that `--profile` and `--select` are mutually
   exclusive.
2. **Given** a config with profile `emea`, **When** the user runs `twmcp
   compile <agent> --profile emea --interactive`, **Then** the interactive
   menu opens with the profile's member servers pre-selected and the user
   can confirm or refine the selection.

---

### Edge Cases

- **Empty profile**: `emea = []` is allowed and produces an empty server set
  (same outcome as `--select none`). Documented behavior, not an error.
- **Duplicate server names within a profile**: `emea = ["server-a",
  "server-a"]` is treated as `["server-a"]` (deduplicated, no warning).
- **Profile name conflicts with a server name**: Profiles and servers live
  in separate namespaces; a profile may share a name with a server without
  conflict.
- **Profile names**: Must be non-empty strings. No nesting (a profile
  cannot reference another profile) — keep it flat for v1.
- **`--all` agents with `--profile`**: The same profile filter applies
  uniformly to every compiled agent.
- **Profile-selected server an agent can't represent**: Behaves the same as
  today's non-profile path — a `Warning: Skipping server '...'` is written
  to stderr and the rest of the compile continues. Profile membership does
  not promote this to an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The canonical config MUST support an optional `[profiles]`
  TOML table where each key is a profile name and each value is a list of
  server names drawn from `[servers]`.
- **FR-002**: The `compile` command MUST accept a `--profile <name>` flag
  that restricts the compiled output to the servers listed in the named
  profile.
- **FR-003**: The system MUST fail with a clear, actionable error message
  when `--profile` references a name that does not exist in `[profiles]`,
  listing the available profile names.
- **FR-004**: The system MUST fail with a clear, actionable error message
  when a profile references a server name not present in `[servers]`,
  naming each missing server.
- **FR-005**: `--profile` MUST be mutually exclusive with both `--select`
  and `--interactive`, except that `--profile` combined with `--interactive`
  pre-seeds the interactive picker with the profile's servers (P3).
- **FR-006**: The system MUST provide a `twmcp profiles` command that lists
  all defined profiles with their member server names, with an optional
  `--json` flag for machine-readable output and a `--config <path>` flag
  consistent with other commands.
- **FR-007**: When `--profile` is used together with `--all`, the same
  profile filter MUST apply to every compiled agent.
- **FR-008**: When the user runs `compile` without `--profile`, behavior
  MUST be unchanged (all servers compiled, same as today).
- **FR-009**: The system MUST validate `[profiles]` at config load time —
  invalid types (non-list values, non-string entries) cause a clear load
  error before any compilation begins.
- **FR-010**: Debug logging (already wired to `-v`) MUST surface which
  profile was selected, how many servers it contains, and which servers
  were excluded.

### Key Entities

- **Profile**: A named, ordered list of server names. Lives in the
  `[profiles]` section of the canonical config. Has no behavior of its own
  — it is a saved selection that can be passed to `compile` to filter the
  server set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with 20 servers can compile a 3-server subset by
  typing `--profile <name>` instead of a comma-separated list of 3 server
  names — saving keystrokes scales linearly with profile size.
- **SC-002**: A user can list every profile and its members with a single
  command (`twmcp profiles`) without opening or grepping the config file.
- **SC-003**: 100% of profile-related errors (missing profile, missing
  server reference, mutual-exclusion conflicts) produce a single-screen
  error message naming the offending input and listing valid alternatives
  where applicable.
- **SC-004**: Existing configs without `[profiles]` continue to compile
  with no behavioral change — zero regressions in the existing test suite
  after the feature lands.

## Assumptions

- **Profiles are flat**: A profile lists server names only; it cannot
  reference another profile. Nesting is out of scope for v1.
- **Profiles are TOML-native**: They live in the existing canonical config
  file, not in a separate file or environment variable. This matches how
  `[agents.*]` overrides are already structured.
- **Profile names are arbitrary strings**: No reserved-word list. The CLI
  parses `--profile <name>` as a single token; names with spaces or shell
  metacharacters are the user's problem to quote.
- **Order does not matter**: A profile's server list is treated as a set
  for filtering; output ordering follows the existing `[servers]` ordering
  in the canonical config (consistent with current `--select` behavior).
- **`extract` is unchanged**: The reverse `extract` command, which reads
  agent JSON and writes canonical TOML, does not need to emit profiles.
  Profiles are an authored construct, not something that exists in compiled
  agent output.
