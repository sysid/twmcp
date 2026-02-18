import json

import pytest
from typer.testing import CliRunner

from twmcp.cli import app

runner = CliRunner()


class TestCompileCommand:
    def test_dry_run_outputs_valid_json(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "mcpServers" in output

    def test_dry_run_copilot_cli_structure(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        output = json.loads(result.stdout)
        assert "github" in output["mcpServers"]
        assert "atlassian" in output["mcpServers"]
        assert "local-proxy" in output["mcpServers"]

    def test_dry_run_intellij_nested_headers(self, sample_config_path):
        result = runner.invoke(
            app,
            ["compile", "intellij", "--config", str(sample_config_path), "--dry-run"],
        )
        output = json.loads(result.stdout)
        assert "servers" in output
        atlassian = output["servers"]["atlassian"]
        assert "requestInit" in atlassian

    def test_dry_run_claude_desktop_skips_http(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "claude-desktop",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        output = json.loads(result.stdout)
        assert "atlassian" not in output["mcpServers"]

    def test_unknown_agent_exits_1(self, sample_config_path):
        result = runner.invoke(
            app,
            ["compile", "nonexistent-agent", "--config", str(sample_config_path)],
        )
        assert result.exit_code == 1

    def test_unknown_agent_error_message(self, sample_config_path):
        result = runner.invoke(
            app,
            ["compile", "nonexistent-agent", "--config", str(sample_config_path)],
        )
        assert "unknown agent" in result.stdout.lower()

    def test_config_flag_overrides_default(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

    def test_missing_config_exits_1(self, tmp_path):
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(tmp_path / "nonexistent.toml")],
        )
        assert result.exit_code == 1

    def test_missing_config_error_message(self, tmp_path):
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(tmp_path / "nonexistent.toml")],
        )
        assert "not found" in result.stdout.lower()

    def test_compile_writes_file(self, sample_config_path, tmp_path, monkeypatch):
        """Non-dry-run compile writes JSON to the agent's config path."""
        output_file = tmp_path / "output" / "mcp-config.json"
        monkeypatch.setattr(
            "twmcp.agents.AGENT_REGISTRY",
            {
                "copilot-cli": pytest.importorskip("twmcp.agents").AgentProfile(
                    name="copilot-cli",
                    config_path=output_file,
                    top_level_key="mcpServers",
                    type_mapping={"stdio": "local"},
                    header_style="flat",
                ),
            },
        )
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(sample_config_path)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert "mcpServers" in content


class TestCompileAll:
    """Test --all flag for compile command (T018)."""

    def test_all_dry_run_outputs_all_agents(self, sample_config_path):
        result = runner.invoke(
            app,
            ["compile", "--all", "--config", str(sample_config_path), "--dry-run"],
        )
        assert result.exit_code == 0
        output = result.stdout
        assert "copilot-cli" in output
        assert "intellij" in output
        assert "claude-desktop" in output

    def test_all_dry_run_has_valid_json_per_agent(self, sample_config_path):
        result = runner.invoke(
            app,
            ["compile", "--all", "--config", str(sample_config_path), "--dry-run"],
        )
        assert result.exit_code == 0
        # Each agent section should contain valid JSON-like content
        assert "mcpServers" in result.stdout  # copilot-cli and claude-desktop
        assert "servers" in result.stdout  # intellij

    def test_all_writes_files(self, sample_config_path, tmp_path, monkeypatch):
        from twmcp.agents import AgentProfile

        monkeypatch.setattr(
            "twmcp.agents.AGENT_REGISTRY",
            {
                "agent-a": AgentProfile(
                    name="agent-a",
                    config_path=tmp_path / "a.json",
                    top_level_key="mcpServers",
                    type_mapping={"stdio": "local"},
                    header_style="flat",
                ),
                "agent-b": AgentProfile(
                    name="agent-b",
                    config_path=tmp_path / "b.json",
                    top_level_key="servers",
                    type_mapping={},
                    header_style="nested",
                ),
            },
        )
        result = runner.invoke(
            app,
            ["compile", "--all", "--config", str(sample_config_path)],
        )
        assert result.exit_code == 0
        assert (tmp_path / "a.json").exists()
        assert (tmp_path / "b.json").exists()

    def test_all_without_agent_argument(self, sample_config_path):
        """--all should work without specifying an agent name."""
        result = runner.invoke(
            app,
            ["compile", "--all", "--config", str(sample_config_path), "--dry-run"],
        )
        assert result.exit_code == 0


class TestAgentsCommand:
    """Test agents command (T020)."""

    def test_agents_lists_all(self):
        result = runner.invoke(app, ["agents"])
        assert result.exit_code == 0
        assert "copilot-cli" in result.stdout
        assert "intellij" in result.stdout
        assert "claude-desktop" in result.stdout

    def test_agents_shows_config_paths(self):
        result = runner.invoke(app, ["agents"])
        assert result.exit_code == 0
        assert "mcp-config.json" in result.stdout
        assert "mcp.json" in result.stdout

    def test_agents_json_output(self):
        result = runner.invoke(app, ["agents", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 3
        names = {a["name"] for a in data}
        assert names == {"copilot-cli", "intellij", "claude-desktop"}

    def test_agents_json_has_required_fields(self):
        result = runner.invoke(app, ["agents", "--json"])
        data = json.loads(result.stdout)
        for agent in data:
            assert "name" in agent
            assert "config_path" in agent
            assert "top_level_key" in agent


class TestCompileWithInterpolation:
    """Test variable interpolation through the CLI (T015)."""

    def test_env_vars_resolved_in_output(self, sample_config_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "cli-test-token")
        monkeypatch.setenv("CONFLUENCE_TOKEN", "cli-confluence-token")
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        github_env = output["mcpServers"]["github"]["env"]
        assert github_env["GITHUB_TOKEN"] == "cli-test-token"

    def test_dotenv_values_used(self, sample_config_path, monkeypatch):
        """Values from secrets.env should be used when env vars not set."""
        # Clear env vars so dotenv values are used
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)
        monkeypatch.delenv("API_TOKEN", raising=False)
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        github_env = output["mcpServers"]["github"]["env"]
        assert github_env["GITHUB_TOKEN"] == "ghp_test123"  # from secrets.env

    def test_env_var_overrides_dotenv(self, sample_config_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "env-override")
        monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["mcpServers"]["github"]["env"]["GITHUB_TOKEN"] == "env-override"

    def test_default_value_used(self, sample_config_path, monkeypatch):
        """${API_TOKEN:-default-token} should use default when neither env nor dotenv set."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)
        monkeypatch.delenv("API_TOKEN", raising=False)
        # Remove API_TOKEN from dotenv by using a config without dotenv
        config = sample_config_path.parent / "no_dotenv_config.toml"
        config.write_text(
            "[servers.test]\n"
            'command = "test"\n'
            'type = "stdio"\n'
            "[servers.test.env]\n"
            'TOKEN = "${API_TOKEN:-default-token}"\n'
        )
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(config), "--dry-run"],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["mcpServers"]["test"]["env"]["TOKEN"] == "default-token"

    def test_unresolved_variable_exits_1(self, tmp_path, monkeypatch):
        config = tmp_path / "config.toml"
        config.write_text(
            "[servers.test]\n"
            'command = "test"\n'
            'type = "stdio"\n'
            "[servers.test.env]\n"
            'SECRET = "${TOTALLY_MISSING_VAR}"\n'
        )
        monkeypatch.delenv("TOTALLY_MISSING_VAR", raising=False)
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(config)],
        )
        assert result.exit_code == 1

    def test_unresolved_variable_error_lists_all(self, tmp_path, monkeypatch):
        config = tmp_path / "config.toml"
        config.write_text(
            "[servers.test]\n"
            'command = "test"\n'
            'type = "stdio"\n'
            "[servers.test.env]\n"
            'A = "${MISSING_A}"\n'
            'B = "${MISSING_B}"\n'
        )
        monkeypatch.delenv("MISSING_A", raising=False)
        monkeypatch.delenv("MISSING_B", raising=False)
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(config)],
        )
        assert result.exit_code == 1
        assert "MISSING_A" in result.stdout
        assert "MISSING_B" in result.stdout

    def test_missing_dotenv_error_not_misleading(self, tmp_path):
        """Missing env_file must say 'Dotenv file not found', not 'Config file not found'."""
        config = tmp_path / "config.toml"
        config.write_text(
            'env_file = "secrets.env"\n'
            "[servers.test]\n"
            'command = "test"\n'
            'type = "stdio"\n'
        )
        result = runner.invoke(
            app,
            ["compile", "copilot-cli", "--config", str(config)],
        )
        assert result.exit_code == 1
        assert "dotenv" in result.stdout.lower()
        assert "config file not found" not in result.stdout.lower()
