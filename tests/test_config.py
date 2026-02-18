import pytest

from twmcp.config import load_config, CanonicalConfig, Server


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
