from pathlib import Path

import pytest

from twmcp.agents import (
    AgentProfile,
    get_profile,
    list_agents,
    resolve_profile,
    AGENT_REGISTRY,
)


class TestAgentProfile:
    def test_profile_has_required_fields(self):
        profile = get_profile("copilot-cli")
        assert isinstance(profile, AgentProfile)
        assert profile.name == "copilot-cli"
        assert profile.config_path is not None
        assert profile.top_level_key in ("mcpServers", "servers")
        assert isinstance(profile.type_mapping, dict)
        assert profile.header_style in ("flat", "nested", "none")

    def test_copilot_cli_profile(self):
        p = get_profile("copilot-cli")
        assert p.top_level_key == "mcpServers"
        assert p.type_mapping == {"stdio": "local"}
        assert p.header_style == "flat"
        assert p.config_path == Path(".copilot") / "mcp-config.json"

    def test_intellij_profile(self):
        p = get_profile("intellij")
        assert p.top_level_key == "servers"
        assert p.type_mapping == {}
        assert p.header_style == "nested"

    def test_claude_desktop_profile(self):
        p = get_profile("claude-desktop")
        assert p.top_level_key == "mcpServers"
        assert p.header_style == "none"

    def test_claude_code_profile(self):
        p = get_profile("claude-code")
        assert p.name == "claude-code"
        assert p.config_path == Path(".mcp.json")
        assert p.top_level_key == "mcpServers"
        assert p.type_mapping == {}
        assert p.header_style == "flat"

    def test_unknown_agent_raises(self):
        with pytest.raises(KeyError, match="unknown-agent"):
            get_profile("unknown-agent")

    def test_list_agents_returns_all(self):
        agents = list_agents()
        names = {a.name for a in agents}
        assert names == {"copilot-cli", "intellij", "claude-desktop", "claude-code"}

    def test_registry_has_four_agents(self):
        assert len(AGENT_REGISTRY) == 4


class TestResolveProfile:
    def test_no_override_returns_registry_entry(self):
        p = resolve_profile("claude-code", {})
        assert p is AGENT_REGISTRY["claude-code"]

    def test_override_expands_user_home(self):
        p = resolve_profile("claude-code", {"claude-code": "~/foo.json"})
        assert p.config_path == Path.home() / "foo.json"
        assert p.top_level_key == "mcpServers"  # non-path fields preserved
        assert p.header_style == "flat"

    def test_override_absolute_path(self):
        p = resolve_profile("claude-desktop", {"claude-desktop": "/tmp/x.json"})
        assert p.config_path == Path("/tmp/x.json")

    def test_override_only_applies_to_named_agent(self):
        overrides = {"claude-code": "/tmp/c.json"}
        p = resolve_profile("claude-desktop", overrides)
        assert p is AGENT_REGISTRY["claude-desktop"]

    def test_unknown_agent_raises(self):
        with pytest.raises(KeyError):
            resolve_profile("nope", {"nope": "/tmp/x.json"})
