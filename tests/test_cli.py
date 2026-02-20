import json
from unittest.mock import patch

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


class TestExtractCommand:
    """Test twmcp extract command."""

    def test_extract_success_exit_code(self, fixtures_dir):
        result = runner.invoke(
            app, ["extract", str(fixtures_dir / "claude_desktop.json")]
        )
        assert result.exit_code == 0

    def test_extract_outputs_valid_toml(self, fixtures_dir):
        result = runner.invoke(
            app, ["extract", str(fixtures_dir / "claude_desktop.json")]
        )
        assert "[servers.github]" in result.stdout
        assert "[servers.local-proxy]" in result.stdout

    def test_extract_contains_header_comment(self, fixtures_dir):
        result = runner.invoke(
            app, ["extract", str(fixtures_dir / "claude_desktop.json")]
        )
        assert "# Generated by: twmcp extract" in result.stdout

    def test_extract_secrets_replaced(self, fixtures_dir):
        result = runner.invoke(
            app, ["extract", str(fixtures_dir / "claude_desktop.json")]
        )
        assert "${GITHUB_TOKEN}" in result.stdout
        assert "ghp_abc123def456" not in result.stdout

    def test_extract_file_not_found(self, tmp_path):
        result = runner.invoke(app, ["extract", str(tmp_path / "nonexistent.json")])
        assert result.exit_code == 1

    def test_extract_invalid_json(self, tmp_path):
        bad_file = tmp_path / "broken.json"
        bad_file.write_text("{invalid json")
        result = runner.invoke(app, ["extract", str(bad_file)])
        assert result.exit_code == 1

    def test_extract_no_servers(self, tmp_path):
        empty_file = tmp_path / "empty.json"
        empty_file.write_text('{"unrelated": "data"}')
        result = runner.invoke(app, ["extract", str(empty_file)])
        assert result.exit_code == 1


class TestCompileSelectNone:
    """Test --select none for empty configuration (US2)."""

    def test_select_none_produces_empty_config(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "none",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output == {"mcpServers": {}}

    def test_select_none_with_all(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "--all",
                "--config",
                str(sample_config_path),
                "--select",
                "none",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        # All agent sections should have empty server maps
        assert "github" not in result.stdout
        assert "atlassian" not in result.stdout
        assert "local-proxy" not in result.stdout

    def test_select_empty_string_exits_1(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "",
            ],
        )
        assert result.exit_code == 1
        assert "--select none" in result.stdout

    def test_select_whitespace_exits_1(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                " , ",
            ],
        )
        assert result.exit_code == 1


class TestCompileInteractive:
    """Test --interactive flag for interactive server selection (US3)."""

    @patch("twmcp.cli.is_interactive_terminal", return_value=True)
    @patch("twmcp.cli.select_servers_interactive")
    def test_interactive_calls_menu(self, mock_select, mock_tty, sample_config_path):
        mock_select.return_value = ["github", "local-proxy"]
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "github" in output["mcpServers"]
        assert "local-proxy" in output["mcpServers"]
        assert "atlassian" not in output["mcpServers"]

    @patch("twmcp.cli.is_interactive_terminal", return_value=True)
    @patch("twmcp.cli.select_servers_interactive")
    def test_interactive_cancelled_exits_0(
        self, mock_select, mock_tty, sample_config_path
    ):
        mock_select.return_value = None
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

    @patch("twmcp.cli.is_interactive_terminal", return_value=True)
    @patch("twmcp.cli.select_servers_interactive")
    def test_interactive_empty_produces_empty_config(
        self, mock_select, mock_tty, sample_config_path
    ):
        """Enter without selecting → empty config output, not first server."""
        mock_select.return_value = []
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output == {"mcpServers": {}}

    @patch("twmcp.cli.is_interactive_terminal", return_value=False)
    def test_interactive_non_tty_exits_1(self, mock_tty, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 1
        assert "interactive terminal" in result.stdout.lower()


class TestCompileSelectNonInteractive:
    """Test --select <value> non-interactive filter mode (US2)."""

    def test_select_value_filters_servers(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "github,local-proxy",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "github" in output["mcpServers"]
        assert "local-proxy" in output["mcpServers"]
        assert "atlassian" not in output["mcpServers"]

    def test_select_single_server(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "github",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "github" in output["mcpServers"]
        assert len(output["mcpServers"]) == 1

    def test_select_unknown_server_exits_1(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "nonexistent",
            ],
        )
        assert result.exit_code == 1
        assert "nonexistent" in result.stdout.lower()

    def test_select_unknown_lists_available(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "nonexistent",
            ],
        )
        assert result.exit_code == 1
        assert "github" in result.stdout

    def test_select_mixed_valid_invalid_exits_1(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "github,bogus",
            ],
        )
        assert result.exit_code == 1
        assert "bogus" in result.stdout.lower()

    def test_select_equals_syntax(self, sample_config_path):
        """--select=github should work the same as --select github."""
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select=github",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "github" in output["mcpServers"]
        assert len(output["mcpServers"]) == 1


class TestCompileSelectWithAll:
    """Test --all with --select and --interactive combinations."""

    @patch("twmcp.cli.is_interactive_terminal", return_value=True)
    @patch("twmcp.cli.select_servers_interactive")
    def test_all_interactive_called_once(
        self, mock_select, mock_tty, sample_config_path
    ):
        mock_select.return_value = ["github", "local-proxy"]
        result = runner.invoke(
            app,
            [
                "compile",
                "--all",
                "--config",
                str(sample_config_path),
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        mock_select.assert_called_once()

    @patch("twmcp.cli.is_interactive_terminal", return_value=True)
    @patch("twmcp.cli.select_servers_interactive")
    def test_all_interactive_filters_all_agents(
        self, mock_select, mock_tty, sample_config_path
    ):
        mock_select.return_value = ["github", "local-proxy"]
        result = runner.invoke(
            app,
            [
                "compile",
                "--all",
                "--config",
                str(sample_config_path),
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        # atlassian should not appear in any agent output
        assert "atlassian" not in result.stdout

    def test_all_select_value_filters_all_agents(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "--all",
                "--config",
                str(sample_config_path),
                "--select",
                "github,local-proxy",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "atlassian" not in result.stdout

    def test_all_select_value_incompatible_still_skipped(self, sample_config_path):
        """claude-desktop skips http servers; --select of http-only should produce empty for that agent."""
        result = runner.invoke(
            app,
            [
                "compile",
                "--all",
                "--config",
                str(sample_config_path),
                "--select",
                "atlassian",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        # claude-desktop section should have no servers since atlassian is http
        output = result.stdout
        assert "claude-desktop" in output


class TestCompileSelectInteractiveMutualExclusivity:
    """Test --select and --interactive mutual exclusivity (US4)."""

    def test_select_and_interactive_exits_1(self, sample_config_path):
        result = runner.invoke(
            app,
            [
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--select",
                "github",
                "--interactive",
                "--dry-run",
            ],
        )
        assert result.exit_code == 1
        assert "mutually exclusive" in result.stdout.lower()


class TestVersionFlag:
    """Test --version / -V flag and hidden version command."""

    def test_version_long_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "twmcp version:" in result.stdout.lower()

    def test_version_short_flag(self):
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "twmcp version:" in result.stdout.lower()

    def test_version_contains_semver(self):
        """Version output should contain a semver-like string."""
        import re

        result = runner.invoke(app, ["--version"])
        assert re.search(r"\d+\.\d+\.\d+", result.stdout)

    def test_version_hidden_command(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "twmcp version:" in result.stdout.lower()


class TestVerboseFlag:
    """Test --verbose / -v flag configures logging."""

    def test_verbose_long_flag_accepted(self, sample_config_path):
        """--verbose should be accepted without error."""
        result = runner.invoke(
            app,
            [
                "--verbose",
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

    def test_verbose_short_flag_accepted(self, sample_config_path):
        """-v should be accepted without error."""
        result = runner.invoke(
            app,
            [
                "-v",
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

    def test_verbose_sets_debug_logging(self, sample_config_path):
        """--verbose should configure root logger to DEBUG level."""
        import logging

        result = runner.invoke(
            app,
            [
                "--verbose",
                "compile",
                "copilot-cli",
                "--config",
                str(sample_config_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert logging.getLogger().level == logging.DEBUG


class TestBareInvocation:
    """Test bare invocation (no subcommand, no flags) shows help."""

    def test_bare_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "compile" in result.stdout.lower()
        assert "agents" in result.stdout.lower()
        assert "extract" in result.stdout.lower()
