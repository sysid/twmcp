# Quickstart: Project-Local Agent Configurations

## What Changes

1. **New agent**: `claude-code` — writes to `.claude/mcp-config.json` (project-local)
2. **Changed agent**: `copilot-cli` — writes to `.copilot/mcp-config.json` (project-local, was global `~/.copilot/mcp-config.json`)

## Files to Modify

| File | Change |
|------|--------|
| `src/twmcp/agents.py` | Add `claude-code` profile, change `copilot-cli` path to relative |
| `tests/test_agents.py` | Add claude-code tests, update copilot-cli path test, update agent count |
| `tests/test_compiler.py` | Add claude-code transform tests (type included, flat headers, http/sse supported) |

## Claude-Code AgentProfile

```python
"claude-code": AgentProfile(
    name="claude-code",
    config_path=Path(".claude") / "mcp-config.json",
    top_level_key="mcpServers",
    type_mapping={},
    header_style="flat",
),
```

## Copilot-CLI Path Change

```python
# Before
config_path=Path.home() / ".copilot" / "mcp-config.json",
# After
config_path=Path(".copilot") / "mcp-config.json",
```

## Verification

```bash
# Test claude-code output
uv run twmcp compile claude-code --dry-run --config tests/fixtures/sample_config.toml

# Test copilot-cli still works
uv run twmcp compile copilot-cli --dry-run --config tests/fixtures/sample_config.toml

# Run tests
uv run python -m pytest tests/ -v
```
