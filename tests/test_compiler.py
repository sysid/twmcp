import json

import pytest

from twmcp.agents import get_profile
from twmcp.compiler import transform_for_agent, write_config
from twmcp.config import CanonicalConfig, PartialServer, Server


@pytest.fixture
def simple_config():
    """Config with literal values for testing transformation logic."""
    return CanonicalConfig(
        servers={
            "github": Server(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                type="stdio",
                env={"GITHUB_TOKEN": "test-token"},
                overrides={
                    "copilot-cli": PartialServer(type="local"),
                },
            ),
            "atlassian": Server(
                type="http",
                url="https://atc.bmwgroup.net/mcp/",
                headers={
                    "X-Atlassian-Token": "test-token",
                    "X-Atlassian-Url": "https://example.com",
                },
                tools=["*"],
            ),
            "local-proxy": Server(
                command="mcp-proxy",
                args=["http://localhost:8113/sse"],
                type="stdio",
                env={"API_TOKEN": "test-api-token"},
            ),
        },
    )


class TestTransformForAgent:
    def test_copilot_cli_top_level_key(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        assert "mcpServers" in result

    def test_copilot_cli_includes_all_servers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        assert set(result["mcpServers"].keys()) == {
            "github",
            "atlassian",
            "local-proxy",
        }

    def test_copilot_cli_type_mapping(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        # stdio → local for copilot-cli
        assert result["mcpServers"]["local-proxy"]["type"] == "local"
        # http stays http
        assert result["mcpServers"]["atlassian"]["type"] == "http"

    def test_copilot_cli_override_applied(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        assert result["mcpServers"]["github"]["type"] == "local"

    def test_copilot_cli_flat_headers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        atlassian = result["mcpServers"]["atlassian"]
        assert "headers" in atlassian
        assert "requestInit" not in atlassian

    def test_copilot_cli_server_fields(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        github = result["mcpServers"]["github"]
        assert github["command"] == "npx"
        assert github["args"] == ["-y", "@modelcontextprotocol/server-github"]
        assert github["env"] == {"GITHUB_TOKEN": "test-token"}

    def test_intellij_top_level_key(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("intellij"))
        assert "servers" in result

    def test_intellij_no_type_mapping(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("intellij"))
        assert result["servers"]["github"]["type"] == "stdio"

    def test_intellij_nested_headers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("intellij"))
        atlassian = result["servers"]["atlassian"]
        assert "requestInit" in atlassian
        assert "headers" in atlassian["requestInit"]
        assert atlassian["requestInit"]["headers"]["X-Atlassian-Token"] == "test-token"
        # flat headers key must not be present alongside requestInit
        assert "headers" not in atlassian

    def test_claude_desktop_skips_http_servers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-desktop"))
        assert "atlassian" not in result["mcpServers"]

    def test_claude_desktop_omits_type_field(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-desktop"))
        github = result["mcpServers"]["github"]
        assert "type" not in github

    def test_claude_desktop_includes_stdio_servers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-desktop"))
        assert "github" in result["mcpServers"]
        assert "local-proxy" in result["mcpServers"]

    def test_claude_desktop_server_fields(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-desktop"))
        github = result["mcpServers"]["github"]
        assert github["command"] == "npx"
        assert github["args"] == ["-y", "@modelcontextprotocol/server-github"]
        assert github["env"] == {"GITHUB_TOKEN": "test-token"}

    def test_claude_code_includes_all_servers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-code"))
        assert set(result["mcpServers"].keys()) == {
            "github",
            "atlassian",
            "local-proxy",
        }

    def test_claude_code_includes_type_field(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-code"))
        github = result["mcpServers"]["github"]
        assert "type" in github
        assert github["type"] == "stdio"

    def test_claude_code_flat_headers(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("claude-code"))
        atlassian = result["mcpServers"]["atlassian"]
        assert "headers" in atlassian
        assert "requestInit" not in atlassian
        assert atlassian["headers"]["X-Atlassian-Token"] == "test-token"

    def test_override_merges_partial(self):
        """Override only replaces specified fields, preserves others."""
        config = CanonicalConfig(
            servers={
                "test": Server(
                    command="original-cmd",
                    args=["--flag"],
                    type="stdio",
                    env={"KEY": "value"},
                    overrides={
                        "copilot-cli": PartialServer(command="override-cmd"),
                    },
                ),
            },
        )
        result = transform_for_agent(config, get_profile("copilot-cli"))
        server = result["mcpServers"]["test"]
        assert server["command"] == "override-cmd"
        assert server["args"] == ["--flag"]
        assert server["env"] == {"KEY": "value"}

    def test_skipped_server_warns_stderr(self, simple_config, capsys):
        """Skipping an http server for claude-desktop should warn on stderr."""
        transform_for_agent(simple_config, get_profile("claude-desktop"))
        captured = capsys.readouterr()
        assert "atlassian" in captured.err

    def test_empty_env_not_included(self):
        """Server with empty env dict should not have env key in output."""
        config = CanonicalConfig(
            servers={
                "minimal": Server(command="test-cmd", type="stdio"),
            },
        )
        result = transform_for_agent(config, get_profile("copilot-cli"))
        assert "env" not in result["mcpServers"]["minimal"]

    def test_http_server_fields(self, simple_config):
        result = transform_for_agent(simple_config, get_profile("copilot-cli"))
        atlassian = result["mcpServers"]["atlassian"]
        assert atlassian["url"] == "https://atc.bmwgroup.net/mcp/"
        assert atlassian["tools"] == ["*"]
        # http server should not have command/args
        assert "command" not in atlassian
        assert "args" not in atlassian


class TestWriteConfig:
    def test_writes_valid_json(self, tmp_path):
        output = tmp_path / "test.json"
        data = {"mcpServers": {"github": {"command": "npx"}}}
        write_config(data, output)
        assert output.exists()
        assert json.loads(output.read_text()) == data

    def test_json_uses_indent_2(self, tmp_path):
        output = tmp_path / "test.json"
        data = {"mcpServers": {"github": {"command": "npx"}}}
        write_config(data, output)
        text = output.read_text()
        assert '\n  "mcpServers"' in text

    def test_creates_parent_directories(self, tmp_path):
        output = tmp_path / "sub" / "dir" / "test.json"
        data = {"mcpServers": {}}
        write_config(data, output)
        assert output.exists()

    def test_trailing_newline(self, tmp_path):
        output = tmp_path / "test.json"
        write_config({"key": "value"}, output)
        assert output.read_text().endswith("\n")
