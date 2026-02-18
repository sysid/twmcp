import os

import pytest

from twmcp.interpolate import load_dotenv, resolve_variables


class TestResolveVariables:
    def test_simple_variable(self):
        result = resolve_variables("${FOO}", {"FOO": "bar"})
        assert result == "bar"

    def test_variable_with_default_uses_value(self):
        result = resolve_variables("${FOO:-fallback}", {"FOO": "bar"})
        assert result == "bar"

    def test_variable_with_default_uses_default(self):
        result = resolve_variables("${FOO:-fallback}", {})
        assert result == "fallback"

    def test_multiple_variables_in_string(self):
        result = resolve_variables(
            "https://${HOST}:${PORT}/api",
            {"HOST": "example.com", "PORT": "8080"},
        )
        assert result == "https://example.com:8080/api"

    def test_literal_string_unchanged(self):
        result = resolve_variables("no variables here", {"FOO": "bar"})
        assert result == "no variables here"

    def test_empty_string(self):
        result = resolve_variables("", {})
        assert result == ""

    def test_unresolved_variable_raises(self):
        with pytest.raises(ValueError, match="MISSING_VAR"):
            resolve_variables("${MISSING_VAR}", {})

    def test_unresolved_lists_all_missing(self):
        """Error message should list ALL unresolved variables, not just the first."""
        with pytest.raises(ValueError, match="VAR_A") as exc_info:
            resolve_variables("${VAR_A} and ${VAR_B}", {})
        assert "VAR_B" in str(exc_info.value)

    def test_variable_with_underscore(self):
        result = resolve_variables("${MY_VAR}", {"MY_VAR": "value"})
        assert result == "value"

    def test_variable_with_empty_default(self):
        """${VAR:-} should resolve to empty string when VAR not set."""
        result = resolve_variables("${VAR:-}", {})
        assert result == ""

    def test_default_with_special_chars(self):
        result = resolve_variables("${VAR:-https://example.com/path}", {})
        assert result == "https://example.com/path"


class TestLoadDotenv:
    def test_loads_key_value_pairs(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        result = load_dotenv(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_skips_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nFOO=bar\n")
        result = load_dotenv(env_file)
        assert result == {"FOO": "bar"}

    def test_skips_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\n\n\nBAZ=qux\n")
        result = load_dotenv(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_strips_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=\"bar\"\nBAZ='qux'\n")
        result = load_dotenv(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_value_with_equals(self, tmp_path):
        """Values containing = should be preserved."""
        env_file = tmp_path / ".env"
        env_file.write_text("URL=https://example.com?foo=bar\n")
        result = load_dotenv(env_file)
        assert result == {"URL": "https://example.com?foo=bar"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_dotenv(tmp_path / "nonexistent.env")

    def test_empty_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        result = load_dotenv(env_file)
        assert result == {}


class TestEnvVarPrecedence:
    """Test that environment variables take precedence over dotenv values."""

    def test_env_var_wins_over_dotenv(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=from-dotenv\n")
        dotenv_vars = load_dotenv(env_file)
        monkeypatch.setenv("FOO", "from-env")

        # Build variable map: dotenv first, env vars override
        variables = {**dotenv_vars, **{k: v for k, v in os.environ.items()}}
        result = resolve_variables("${FOO}", variables)
        assert result == "from-env"

    def test_dotenv_used_when_env_not_set(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=from-dotenv\n")
        dotenv_vars = load_dotenv(env_file)
        monkeypatch.delenv("FOO", raising=False)

        variables = {**dotenv_vars}
        result = resolve_variables("${FOO}", variables)
        assert result == "from-dotenv"
