# Research: Project-Local Agent Configurations

**Date**: 2026-03-08

## R1: Claude Code MCP Config Format

**Decision**: claude-code uses `mcpServers` top-level key, includes `type` field, flat `headers`, supports all server types (stdio, http, sse).

**Rationale**: Claude Code's `--mcp-config` flag accepts JSON with the same schema as `.claude/mcp-config.json`. Unlike claude-desktop (which omits `type` and skips http/sse), claude-code supports the full MCP spec including remote servers. Verified from Claude Code documentation.

**Alternatives considered**:
- Same format as claude-desktop (no `type`, skip http/sse) — rejected because claude-code actually supports remote servers
- Same as copilot-cli with `stdio→local` mapping — rejected because claude-code uses standard `stdio` type name

**AgentProfile mapping**:
- `name`: `"claude-code"`
- `config_path`: `Path(".claude") / "mcp-config.json"` (relative)
- `top_level_key`: `"mcpServers"`
- `type_mapping`: `{}` (no remapping)
- `header_style`: `"flat"`

## R2: Project-Local vs Global Paths

**Decision**: Use `Path(".claude/mcp-config.json")` and `Path(".copilot/mcp-config.json")` as relative paths. The existing `write_config()` function resolves these relative to CWD automatically via `Path.parent.mkdir()`.

**Rationale**: `pathlib.Path` with a relative path resolves against CWD at I/O time. No code changes needed in `compiler.py` — `write_config()` already calls `path.parent.mkdir(parents=True, exist_ok=True)` which works with relative paths.

**Alternatives considered**:
- Adding a `resolve_path()` method to AgentProfile — rejected (YAGNI, Path already handles this)
- Adding an `is_project_local` boolean to AgentProfile — rejected (unnecessary complexity, the path itself encodes this)

## R3: Impact on `twmcp agents` Display

**Decision**: Relative paths will display as-is (e.g., `.copilot/mcp-config.json`). The current display logic replaces `Path.home()` with `~` — relative paths won't match, so they'll show their raw form, which is the correct behavior.

**Rationale**: Showing `.copilot/mcp-config.json` makes it clear these are project-local paths. No display code changes needed.

## R4: Breaking Change — copilot-cli Path

**Decision**: Accepted breaking change. copilot-cli moves from `~/.copilot/mcp-config.json` (global) to `.copilot/mcp-config.json` (project-local). No migration path.

**Rationale**: Per constitution and CLAUDE.md — "No backward compatibility without explicit approval by Tom." Tom explicitly requested this change.
