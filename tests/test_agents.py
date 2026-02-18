import pytest

from twmcp.agents import AgentProfile, get_profile, list_agents, AGENT_REGISTRY


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
        assert str(p.config_path).endswith("mcp-config.json")

    def test_intellij_profile(self):
        p = get_profile("intellij")
        assert p.top_level_key == "servers"
        assert p.type_mapping == {}
        assert p.header_style == "nested"

    def test_claude_desktop_profile(self):
        p = get_profile("claude-desktop")
        assert p.top_level_key == "mcpServers"
        assert p.header_style == "none"

    def test_unknown_agent_raises(self):
        with pytest.raises(KeyError, match="unknown-agent"):
            get_profile("unknown-agent")

    def test_list_agents_returns_all(self):
        agents = list_agents()
        names = {a.name for a in agents}
        assert names == {"copilot-cli", "intellij", "claude-desktop"}

    def test_registry_has_three_agents(self):
        assert len(AGENT_REGISTRY) == 3
