import pytest

from twmcp.config import load_config, load_and_resolve, CanonicalConfig, Server


class TestLoadConfig:
    def test_loads_valid_config(self, sample_config_path):
        config = load_config(sample_config_path)
        assert isinstance(config, CanonicalConfig)

    def test_parses_servers(self, sample_config_path):
        config = load_config(sample_config_path)
        assert "github" in config.servers
        assert "atlassian" in config.servers
        assert "local-proxy" in config.servers
        assert len(config.servers) == 3

    def test_parses_env_file(self, sample_config_path):
        config = load_config(sample_config_path)
        assert config.env_file == "secrets.env"

    def test_server_fields(self, sample_config_path):
        config = load_config(sample_config_path)
        github = config.servers["github"]
        assert isinstance(github, Server)
        assert github.command == "npx"
        assert github.args == ["-y", "@modelcontextprotocol/server-github"]
        assert github.type == "stdio"
        assert github.env == {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}

    def test_http_server_fields(self, sample_config_path):
        config = load_config(sample_config_path)
        atlassian = config.servers["atlassian"]
        assert atlassian.type == "http"
        assert atlassian.url == "https://atc.bmwgroup.net/mcp/"
        assert atlassian.tools == ["*"]
        assert "X-Atlassian-Token" in atlassian.headers

    def test_overrides_parsed(self, sample_config_path):
        config = load_config(sample_config_path)
        github = config.servers["github"]
        assert "copilot-cli" in github.overrides
        assert github.overrides["copilot-cli"].type == "local"

    def test_missing_config_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.toml")

    def test_empty_config_raises(self, tmp_path):
        empty = tmp_path / "empty.toml"
        empty.write_text("")
        with pytest.raises(ValueError, match="[Nn]o servers"):
            load_config(empty)

    def test_invalid_toml_raises(self, tmp_path):
        bad = tmp_path / "bad.toml"
        bad.write_text("this is not valid [toml")
        with pytest.raises(Exception):
            load_config(bad)


class TestAgentOverrides:
    def test_parses_agent_overrides(self, sample_config_overrides_path, monkeypatch):
        monkeypatch.setenv("PROJECT_ROOT", "/tmp/fixture-root")
        config = load_and_resolve(sample_config_overrides_path)
        assert config.agent_overrides == {
            "claude-code": "/tmp/fixture-root/claude.json",
            "claude-desktop": "~/custom/claude-desktop.json",
        }

    def test_missing_agents_section_yields_empty_dict(self, sample_config_path):
        config = load_config(sample_config_path)
        assert config.agent_overrides == {}

    def test_unknown_agent_name_raises(self, tmp_path):
        bad = tmp_path / "bad.toml"
        bad.write_text(
            "[agents.does-not-exist]\n"
            'config_path = "/tmp/x.json"\n'
            "\n"
            "[servers.s]\n"
            'command = "echo"\n'
        )
        with pytest.raises(ValueError) as exc:
            load_config(bad)
        msg = str(exc.value)
        assert "does-not-exist" in msg
        assert "claude-code" in msg  # valid agents listed

    def test_non_string_config_path_raises(self, tmp_path):
        bad = tmp_path / "bad.toml"
        bad.write_text(
            '[agents.claude-code]\nconfig_path = 42\n\n[servers.s]\ncommand = "echo"\n'
        )
        with pytest.raises(ValueError) as exc:
            load_config(bad)
        assert "config_path" in str(exc.value)
        assert "string" in str(exc.value)

    def test_empty_agent_section_is_accepted(self, tmp_path):
        cfg = tmp_path / "cfg.toml"
        cfg.write_text('[agents.claude-code]\n\n[servers.s]\ncommand = "echo"\n')
        config = load_config(cfg)
        assert "claude-code" not in config.agent_overrides


class TestProfiles:
    def test_no_profiles_section_yields_empty_dict(self, sample_config_path):
        config = load_config(sample_config_path)
        assert config.profiles == {}

    def test_parses_profiles(self, tmp_path):
        cfg = tmp_path / "cfg.toml"
        cfg.write_text(
            "[profiles]\n"
            'emea = ["a", "b"]\n'
            'apac = ["c"]\n'
            "empty = []\n"
            '\n[servers.a]\ncommand = "echo"\n'
            '[servers.b]\ncommand = "echo"\n'
            '[servers.c]\ncommand = "echo"\n'
        )
        config = load_config(cfg)
        assert config.profiles == {
            "emea": ["a", "b"],
            "apac": ["c"],
            "empty": [],
        }

    def test_profiles_not_a_table_raises(self, tmp_path):
        cfg = tmp_path / "cfg.toml"
        cfg.write_text('profiles = "oops"\n\n[servers.s]\ncommand = "echo"\n')
        with pytest.raises(ValueError) as exc:
            load_config(cfg)
        assert "[profiles]" in str(exc.value)
        assert "table" in str(exc.value)

    def test_profile_value_not_a_list_raises(self, tmp_path):
        cfg = tmp_path / "cfg.toml"
        cfg.write_text(
            '[profiles]\nemea = "server-a"\n\n[servers.s]\ncommand = "echo"\n'
        )
        with pytest.raises(ValueError) as exc:
            load_config(cfg)
        assert "emea" in str(exc.value)
        assert "list" in str(exc.value)

    def test_profile_entry_not_a_string_raises(self, tmp_path):
        cfg = tmp_path / "cfg.toml"
        cfg.write_text(
            '[profiles]\nemea = ["a", 42]\n\n[servers.s]\ncommand = "echo"\n'
        )
        with pytest.raises(ValueError) as exc:
            load_config(cfg)
        assert "emea" in str(exc.value)
        assert "string" in str(exc.value)

    def test_empty_profile_list_is_valid(self, tmp_path):
        cfg = tmp_path / "cfg.toml"
        cfg.write_text('[profiles]\nempty = []\n\n[servers.s]\ncommand = "echo"\n')
        config = load_config(cfg)
        assert config.profiles == {"empty": []}
