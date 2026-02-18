import tomllib
from pathlib import Path

import pytest

from twmcp.extractor import (
    detect_servers,
    extract_from_file,
    format_server_toml,
    is_secret_key,
    normalize_type,
    servers_to_toml,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# --- T002: detect_servers ---


class TestDetectServers:
    def test_mcpservers_format(self):
        data = {"mcpServers": {"github": {"command": "npx"}}}
        assert detect_servers(data) == {"github": {"command": "npx"}}

    def test_vscode_format(self):
        data = {"mcp": {"servers": {"github": {"command": "npx"}}}}
        assert detect_servers(data) == {"github": {"command": "npx"}}

    def test_flat_servers_format(self):
        data = {"servers": {"github": {"command": "npx"}}}
        assert detect_servers(data) == {"github": {"command": "npx"}}

    def test_priority_mcpservers_over_servers(self):
        """mcpServers takes priority when both keys exist."""
        data = {
            "mcpServers": {"a": {"command": "a"}},
            "servers": {"b": {"command": "b"}},
        }
        assert detect_servers(data) == {"a": {"command": "a"}}

    def test_no_recognized_format_raises(self):
        with pytest.raises(ValueError, match="No MCP servers found"):
            detect_servers({"unrelated": "data"})

    def test_empty_servers_raises(self):
        with pytest.raises(ValueError, match="No MCP servers found"):
            detect_servers({"mcpServers": {}})


# --- T003: is_secret_key ---


class TestIsSecretKey:
    @pytest.mark.parametrize(
        "key",
        [
            "GITHUB_TOKEN",
            "API_KEY",
            "DB_PASSWORD",
            "AUTH_SECRET",
            "SERVICE_CREDENTIALS",
        ],
    )
    def test_secret_suffixes_detected(self, key):
        assert is_secret_key(key) is True

    @pytest.mark.parametrize(
        "key",
        [
            "github_token",  # lowercase
            "api_key",
            "db_password",
        ],
    )
    def test_case_insensitive(self, key):
        assert is_secret_key(key) is True

    @pytest.mark.parametrize(
        "key",
        [
            "DEBUG",
            "LOG_LEVEL",
            "HOME",
            "PATH",
            "NODE_ENV",
            "Content-Type",
        ],
    )
    def test_non_secret_keys(self, key):
        assert is_secret_key(key) is False

    def test_header_style_secret(self):
        """Header keys like X-Api-Key should be detected."""
        assert is_secret_key("X-Api-Key") is True
        assert is_secret_key("X-Auth-Token") is True


# --- T004: normalize_type ---


class TestNormalizeType:
    def test_local_to_stdio(self):
        assert normalize_type("local") == "stdio"

    def test_stdio_unchanged(self):
        assert normalize_type("stdio") == "stdio"

    def test_http_unchanged(self):
        assert normalize_type("http") == "http"

    def test_sse_unchanged(self):
        assert normalize_type("sse") == "sse"

    def test_unknown_type_passthrough(self):
        assert normalize_type("custom-transport") == "custom-transport"


# --- T005: TOML formatting ---


class TestFormatServerToml:
    def test_stdio_server_basic(self):
        toml = format_server_toml(
            "github",
            {"command": "npx", "args": ["-y", "server-github"], "type": "stdio"},
        )
        assert "[servers.github]" in toml
        assert 'command = "npx"' in toml
        assert 'args = ["-y", "server-github"]' in toml
        assert 'type = "stdio"' in toml

    def test_env_subtable(self):
        toml = format_server_toml(
            "test",
            {"command": "cmd", "env": {"DEBUG": "true", "HOME": "/usr"}},
        )
        assert "[servers.test.env]" in toml
        assert 'DEBUG = "true"' in toml
        assert 'HOME = "/usr"' in toml

    def test_headers_subtable(self):
        toml = format_server_toml(
            "test",
            {
                "type": "http",
                "url": "https://example.com",
                "headers": {"Content-Type": "application/json"},
            },
        )
        assert "[servers.test.headers]" in toml
        assert 'Content-Type = "application/json"' in toml

    def test_secret_substitution_in_env(self):
        toml = format_server_toml(
            "test",
            {"command": "cmd", "env": {"API_TOKEN": "literal-secret"}},
        )
        assert 'API_TOKEN = "${API_TOKEN}"' in toml
        assert "literal-secret" not in toml

    def test_secret_substitution_in_headers(self):
        toml = format_server_toml(
            "test",
            {
                "type": "http",
                "url": "https://example.com",
                "headers": {"X-Auth-Token": "bearer_xyz"},
            },
        )
        assert 'X-Auth-Token = "${X-Auth-Token}"' in toml
        assert "bearer_xyz" not in toml

    def test_non_secret_env_preserved(self):
        toml = format_server_toml(
            "test",
            {"command": "cmd", "env": {"DEBUG": "true"}},
        )
        assert 'DEBUG = "true"' in toml

    def test_unknown_props_as_comments(self):
        toml = format_server_toml(
            "test",
            {"command": "cmd", "type": "stdio", "disabled": True, "timeout": 30},
        )
        assert "# unknown: disabled = true" in toml
        assert "# unknown: timeout = 30" in toml

    def test_url_field(self):
        toml = format_server_toml(
            "test",
            {"type": "http", "url": "https://example.com/mcp/"},
        )
        assert 'url = "https://example.com/mcp/"' in toml

    def test_tools_field(self):
        toml = format_server_toml(
            "test",
            {"type": "http", "url": "https://example.com", "tools": ["*"]},
        )
        assert 'tools = ["*"]' in toml

    def test_type_normalization_in_output(self):
        toml = format_server_toml(
            "test",
            {"command": "cmd", "type": "local"},
        )
        assert 'type = "stdio"' in toml

    def test_returns_collected_secrets(self):
        _, secrets = format_server_toml(
            "test",
            {"command": "cmd", "env": {"API_TOKEN": "secret", "DEBUG": "true"}},
            return_secrets=True,
        )
        assert "API_TOKEN" in secrets
        assert "DEBUG" not in secrets


class TestServersToToml:
    def test_header_comment_with_source(self):
        servers = {"test": {"command": "cmd"}}
        toml = servers_to_toml(servers, source="input.json")
        assert "# Generated by: twmcp extract input.json" in toml

    def test_header_lists_secret_placeholders(self):
        servers = {
            "svc": {"command": "cmd", "env": {"API_TOKEN": "secret"}},
        }
        toml = servers_to_toml(servers, source="test.json")
        assert "API_TOKEN" in toml.split("\n\n")[0]  # in header comments

    def test_no_secret_header_when_none(self):
        servers = {"svc": {"command": "cmd", "env": {"DEBUG": "true"}}}
        toml = servers_to_toml(servers, source="test.json")
        assert "Secret placeholders" not in toml

    def test_multiple_servers_separated(self):
        servers = {
            "a": {"command": "a-cmd"},
            "b": {"command": "b-cmd"},
        }
        toml = servers_to_toml(servers, source="test.json")
        assert "[servers.a]" in toml
        assert "[servers.b]" in toml


# --- T006: Full pipeline integration ---


class TestExtractFromFile:
    def test_claude_desktop_fixture(self):
        toml_str = extract_from_file(FIXTURES_DIR / "claude_desktop.json")
        # Should be parseable TOML (after replacing ${...} placeholders)
        clean = toml_str.replace("${GITHUB_TOKEN}", "x").replace("${API_TOKEN}", "x")
        parsed = tomllib.loads(clean)
        assert "servers" in parsed
        assert "github" in parsed["servers"]
        assert "local-proxy" in parsed["servers"]

    def test_secrets_replaced_in_output(self):
        toml_str = extract_from_file(FIXTURES_DIR / "claude_desktop.json")
        assert "${GITHUB_TOKEN}" in toml_str
        assert "${API_TOKEN}" in toml_str
        # Literal secrets should NOT appear
        assert "ghp_abc123def456" not in toml_str
        assert "tok_secret_xyz" not in toml_str

    def test_non_secrets_preserved(self):
        toml_str = extract_from_file(FIXTURES_DIR / "claude_desktop.json")
        assert 'DEBUG = "true"' in toml_str

    def test_header_comment_present(self):
        toml_str = extract_from_file(FIXTURES_DIR / "claude_desktop.json")
        assert "# Generated by: twmcp extract" in toml_str

    def test_with_unknown_props(self):
        toml_str = extract_from_file(FIXTURES_DIR / "with_unknown_props.json")
        assert "# unknown: disabled = true" in toml_str
        assert "# unknown: timeout = 30" in toml_str

    def test_with_secrets_fixture(self):
        toml_str = extract_from_file(FIXTURES_DIR / "with_secrets.json")
        assert "${API_TOKEN}" in toml_str
        assert "${API_KEY}" in toml_str
        assert "${DB_PASSWORD}" in toml_str
        assert "${AUTH_SECRET}" in toml_str
        assert "${SERVICE_CREDENTIALS}" in toml_str
        # Non-secrets preserved
        assert 'DEBUG = "true"' in toml_str
        assert 'LOG_LEVEL = "info"' in toml_str
        # Header secrets in headers section
        assert "${X-Api-Key}" in toml_str
        assert "${X-Auth-Token}" in toml_str
        # Non-secret header preserved
        assert 'Content-Type = "application/json"' in toml_str
