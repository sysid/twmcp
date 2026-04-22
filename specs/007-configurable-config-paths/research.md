# Phase 0 Research: Configurable Agent Output Paths

No `NEEDS CLARIFICATION` markers remained after `/speckit.clarify`. This document records the design decisions the plan relies on and the alternatives considered.

## Decisions

### 1. TOML schema shape

**Decision**: `[agents.<name>] config_path = "..."` — one table per agent.

**Rationale**: Mirrors the existing `[servers.<name>]` pattern users already know from the same file. Leaves room for additional per-agent overrides later (e.g., `top_level_key`) without another schema migration.

**Alternatives considered**:
- Flat `[agent_paths] claude-code = "..."` — compact, but boxes future per-agent keys into a second, parallel table.
- Inline tables `agents.claude-code = { config_path = "..." }` — functionally equivalent but less scannable.

### 2. Relative-path resolution

**Decision**: Relative override paths resolve against current working directory (CWD).

**Rationale**: Matches the existing behavior of registry defaults (`.claude/mcp-config.json`, `.copilot/mcp-config.json`) which are `pathlib.Path` instances interpreted by `Path.write_text()` against CWD. Users running `twmcp compile` from a project root get project-local outputs — which is the common case.

**Alternatives considered**:
- Resolve against config-file directory (`~/.config/twmcp/`) — breaks project-local outputs.
- Reject relative paths — safe but hostile to the project-local use case.

### 3. `edit --init` behavior when `config.toml` already exists

**Decision**: Keep existing refuse-to-overwrite behavior unchanged. Existing users who want the defaults block copy from docs or regenerate into a temp file.

**Rationale**: Mutating a user's hand-curated config is high blast-radius and hard to reverse. An "augment" mode would also duplicate content if run twice. YAGNI.

**Alternatives considered**:
- Append commented block when missing — mutates user files, duplicates on re-run.
- Add `--show-defaults` flag that prints to stdout — adds a command surface for negligible benefit; users can `cat` the generated file from a temp init.

### 4. Variable / `~` expansion

**Decision**: Route `config_path` through the existing `_resolve_value` pass in `config.py` so `${VAR}` and `${VAR:-default}` work uniformly. Apply `Path.expanduser()` after interpolation to handle literal `~`.

**Rationale**: Zero new interpolation code. The `_collect_unresolved` pre-scan already surfaces missing variables with a clear error, so unknown `${VAR}` fails fast on load.

**Alternatives considered**:
- Re-implement a separate string expander for paths — duplication.
- Require users to use `${HOME}` instead of `~` — surprising and inconsistent with shell conventions.

### 5. Override application: resolve-on-demand vs mutate registry

**Decision**: Derive an effective `AgentProfile` per invocation via a small helper (`resolve_profile(name, overrides)`). `AGENT_REGISTRY` stays a `frozen=True` immutable source of defaults.

**Rationale**: Immutability keeps tests independent (no global state leak between test cases), keeps `AgentProfile` frozen (dataclass contract), and makes `agents` listing trivially pure.

**Alternatives considered**:
- Mutate `AGENT_REGISTRY` entries at load time — breaks `frozen=True` and introduces global state tied to a specific config load.
- Build a whole new "ResolvedRegistry" dataclass — over-engineered for a dict override lookup.

### 6. `edit --init` template generation

**Decision**: Generate the commented `[agents.*]` block at runtime from `AGENT_REGISTRY` (not hard-coded in a string constant). Future agents added to the registry automatically appear in the seeded template.

**Rationale**: Single source of truth. Zero risk of template drifting from registry. Costs one list comprehension.

**Alternatives considered**:
- Hard-code the block in `DEFAULT_CONFIG_TEMPLATE` — guaranteed to rot when a new agent is added.

### 7. Validation error surface

**Decision**: Raise `ValueError` from config parsing for (a) unknown agent name, (b) non-string `config_path`. `cli._load_config_or_exit` already turns `ValueError` into a user-facing error on stderr with exit code 1 — no new plumbing needed.

**Rationale**: Reuses existing error path. Keeps `config.py` pure (no `typer.Exit`). Message includes the offending key + list of valid agents (FR-006) or actual type (FR-007).

**Alternatives considered**:
- Silent skip of unknown keys — violates fail-fast (constitution + CLAUDE.md).
- Typer-level validation — couples config parsing to CLI framework; harder to unit-test.

### 8. `twmcp agents` effective-path loading

**Decision**: `agents` command gains an optional `--config` flag (default: same as `compile`). It attempts to load config; if file missing or unparseable, falls back to registry defaults with a warning on stderr — the command keeps working without a config present.

**Rationale**: `agents` is a discovery command — it MUST work before the user has written any config (chicken-and-egg). But once a config exists with overrides, displaying registry defaults would actively mislead (FR-011). Warning-plus-fallback threads both needles.

**Alternatives considered**:
- Hard-require config present — breaks first-run UX.
- Silently use defaults — misleads users who expect overrides to be visible.

## Open questions

None. Ready for Phase 1.
