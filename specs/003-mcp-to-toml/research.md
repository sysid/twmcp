# Research: MCP Config to TOML Extractor

**Date**: 2026-02-18
**Feature**: 003-mcp-to-toml

## Decision 1: TOML Generation Approach

**Decision**: Manual string formatting (no external library).

**Rationale**: Python's stdlib has `tomllib` (read-only, no writer). The standard companion `tomli_w` does not support comments. Since FR-009 requires preserving unknown JSON properties as TOML comments, a library-based approach would need post-processing anyway. The output format is constrained and well-defined:
- Simple key-value pairs (strings)
- Arrays of strings (`args`, `tools`)
- Nested tables (`env`, `headers`)
- Comment lines for unknown properties

Manual formatting handles all these patterns cleanly and avoids a new dependency (constitution: "External dependencies MUST be justified").

**Alternatives considered**:
- `tomli_w`: Clean API but no comment support. Would need hybrid approach (generate + post-process), adding complexity with no real benefit.
- `tomlkit`: Preserves comments but is a heavier dependency and overkill for write-only use.

## Decision 2: JSON Format Detection Strategy

**Decision**: Probe for known top-level keys in priority order.

**Rationale**: The agent registry reveals the JSON structures used by each tool:

| Tool | Top-level key | Nested path |
|------|--------------|-------------|
| Claude Desktop | `mcpServers` | `data["mcpServers"]` |
| Copilot CLI | `mcpServers` | `data["mcpServers"]` |
| VS Code | `mcp` | `data["mcp"]["servers"]` |
| IntelliJ | `servers` | `data["servers"]` |

Detection order:
1. `data["mcpServers"]` → Claude Desktop / Copilot CLI
2. `data["mcp"]["servers"]` → VS Code
3. `data["servers"]` → IntelliJ / flat

This is deterministic and covers all known formats. If none match, error with list of expected formats.

**Alternatives considered**:
- Require user to specify format via CLI flag: Rejected — defeats auto-detection goal (FR-002).
- Heuristic based on file path: Fragile, not portable.

## Decision 3: Reverse Type Mapping

**Decision**: Map known agent-specific type names back to canonical types.

**Rationale**: Different agents use different type names for the same transport:
- Copilot CLI: `"local"` → canonical `"stdio"`
- Others: `"stdio"` is already canonical

The reverse mapping is simple:

```
"local" → "stdio"
everything else → pass through as-is
```

Unknown types are preserved with a TOML comment noting they're unrecognized (per edge case spec).

**Alternatives considered**:
- Only support canonical type names: Would break copilot-cli JSON imports.
- Full bidirectional mapping from agent registry: Over-engineered; only `"local"→"stdio"` is needed.

## Decision 4: Secret Detection Pattern

**Decision**: Match env/header key names by suffix pattern.

**Rationale**: Per spec assumption, suffix-based heuristic on key names:

```
Suffixes: _TOKEN, _KEY, _SECRET, _PASSWORD, _CREDENTIALS
```

Applied to both `env` and `headers` dictionaries. When a match is found, the literal value is replaced with `${KEY_NAME}`.

The key name itself becomes the variable name (e.g., `GITHUB_TOKEN = "ghp_abc123"` → `GITHUB_TOKEN = "${GITHUB_TOKEN}"`).

**Alternatives considered**:
- Value-based detection (regex for JWT patterns, hex strings): Higher false-positive rate, more complex, and the spec explicitly chose suffix-based.
- Replace ALL env values: Too aggressive, would obscure non-secret config values.

## Decision 5: Known vs Unknown JSON Properties

**Decision**: Explicit allowlist of known properties; everything else → TOML comment.

**Rationale**: Known server properties (from `config.py:Server` dataclass):

```
command, args, type, env, url, headers, tools
```

Any JSON key in a server entry not in this list is an "unknown property" and gets emitted as a TOML comment: `# unknown: key = value`.

**Alternatives considered**:
- Blocklist (only skip specific known-irrelevant keys): Fragile as new tools add new properties.
- Silently drop: User chose to preserve as comments in clarification.
