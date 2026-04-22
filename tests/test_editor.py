from unittest.mock import patch, MagicMock

import pytest

import tomllib

from twmcp.editor import (
    DEFAULT_CONFIG_TEMPLATE,
    init_config,
    open_in_editor,
    resolve_editor,
)


class TestResolveEditor:
    def test_editor_env_takes_precedence(self):
        with patch.dict("os.environ", {"EDITOR": "nvim", "VISUAL": "code"}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "nvim"
            assert args == []

    def test_visual_fallback_when_editor_unset(self):
        with patch.dict("os.environ", {"VISUAL": "code"}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "code"
            assert args == []

    def test_vi_default_when_no_env(self):
        with patch.dict("os.environ", {}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "vi"
            assert args == []

    def test_editor_with_args_splits_correctly(self):
        with patch.dict("os.environ", {"EDITOR": "code --wait"}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "code"
            assert args == ["--wait"]

    def test_editor_with_multiple_args(self):
        with patch.dict("os.environ", {"EDITOR": "emacs -nw -q"}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "emacs"
            assert args == ["-nw", "-q"]

    def test_empty_editor_falls_to_visual(self):
        with patch.dict("os.environ", {"EDITOR": "", "VISUAL": "nano"}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "nano"
            assert args == []

    def test_empty_editor_and_visual_falls_to_vi(self):
        with patch.dict("os.environ", {"EDITOR": "", "VISUAL": ""}, clear=True):
            cmd, args = resolve_editor()
            assert cmd == "vi"
            assert args == []


class TestOpenInEditor:
    @patch("twmcp.editor.subprocess.run")
    @patch("twmcp.editor.shutil.which", return_value="/usr/bin/vi")
    def test_calls_subprocess_with_correct_args(self, mock_which, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        config = tmp_path / "config.toml"
        config.write_text("[servers]")
        with patch.dict("os.environ", {"EDITOR": "vi"}, clear=True):
            rc = open_in_editor(config)
        mock_run.assert_called_once_with(["vi", str(config)])
        assert rc == 0

    @patch("twmcp.editor.subprocess.run")
    @patch("twmcp.editor.shutil.which", return_value="/usr/bin/code")
    def test_passes_extra_args_from_editor(self, mock_which, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        config = tmp_path / "config.toml"
        config.write_text("[servers]")
        with patch.dict("os.environ", {"EDITOR": "code --wait"}, clear=True):
            open_in_editor(config)
        mock_run.assert_called_once_with(["code", "--wait", str(config)])

    @patch("twmcp.editor.subprocess.run")
    @patch("twmcp.editor.shutil.which", return_value="/usr/bin/vi")
    def test_returns_editor_exit_code(self, mock_which, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=42)
        config = tmp_path / "config.toml"
        config.write_text("[servers]")
        with patch.dict("os.environ", {"EDITOR": "vi"}, clear=True):
            rc = open_in_editor(config)
        assert rc == 42

    @patch("twmcp.editor.shutil.which", return_value=None)
    def test_raises_when_editor_not_found(self, mock_which, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text("[servers]")
        with patch.dict("os.environ", {"EDITOR": "nonexistent"}, clear=True):
            with pytest.raises(FileNotFoundError, match="nonexistent"):
                open_in_editor(config)


class TestDefaultTemplate:
    def test_template_is_valid_toml(self):
        # Comments are stripped by tomllib, but the string must parse
        tomllib.loads(DEFAULT_CONFIG_TEMPLATE)

    def test_template_contains_server_examples(self):
        assert "servers" in DEFAULT_CONFIG_TEMPLATE.lower()

    def test_template_contains_env_file_reference(self):
        assert "env_file" in DEFAULT_CONFIG_TEMPLATE


class TestInitConfig:
    def test_creates_file_with_template(self, tmp_path):
        config = tmp_path / "config.toml"
        init_config(config)
        assert config.exists()
        assert config.read_text() == DEFAULT_CONFIG_TEMPLATE

    def test_creates_parent_directories(self, tmp_path):
        config = tmp_path / "deep" / "nested" / "config.toml"
        init_config(config)
        assert config.exists()
        assert config.read_text() == DEFAULT_CONFIG_TEMPLATE

    def test_raises_when_file_exists(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text("existing content")
        with pytest.raises(FileExistsError, match="already exists"):
            init_config(config)

    def test_existing_file_unchanged_after_error(self, tmp_path):
        config = tmp_path / "config.toml"
        original = "existing content"
        config.write_text(original)
        with pytest.raises(FileExistsError):
            init_config(config)
        assert config.read_text() == original


class TestAgentOverridesInTemplate:
    """Init template must seed a commented [agents.*] block for every registered
    agent so users discover the override mechanism (US2)."""

    def _uncomment_agents_block(self, text: str) -> str:
        # Strip the leading "# " from lines that start an [agents.<name>] or
        # config_path = ... entry. Leaves header/instruction comments alone.
        out = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("# [agents.") or stripped.startswith(
                "# config_path"
            ):
                # Remove the leading "# " (preserving surrounding indentation).
                idx = line.find("# ")
                out.append(line[:idx] + line[idx + 2 :])
            else:
                out.append(line)
        return "\n".join(out)

    def test_template_includes_commented_agents_block(self):
        from twmcp.agents import AGENT_REGISTRY

        for name in AGENT_REGISTRY:
            assert f"# [agents.{name}]" in DEFAULT_CONFIG_TEMPLATE, (
                f"missing seeded block for {name}"
            )

    def test_template_agents_block_uncomments_to_valid_toml(self):
        from twmcp.agents import AGENT_REGISTRY

        uncommented = self._uncomment_agents_block(DEFAULT_CONFIG_TEMPLATE)
        parsed = tomllib.loads(uncommented)
        agents_section = parsed.get("agents", {})
        assert set(agents_section.keys()) == set(AGENT_REGISTRY.keys())
        for name, block in agents_section.items():
            assert "config_path" in block
            assert isinstance(block["config_path"], str)

    def test_template_renders_home_paths_with_tilde(self):
        # Any registry entry under the user's home dir must appear as "~/..."
        # in the seeded block, matching the `twmcp agents` display convention.
        import re
        from pathlib import Path

        home = str(Path.home())
        block_matches = re.findall(
            r'# config_path = "([^"]+)"', DEFAULT_CONFIG_TEMPLATE
        )
        assert block_matches, "no config_path lines found in template"
        for path in block_matches:
            assert home not in path, (
                f"path {path!r} should have been shortened to ~/..."
            )

    def test_init_config_file_contains_agents_block(self, tmp_path):
        config = tmp_path / "config.toml"
        init_config(config)
        text = config.read_text()
        assert "[agents." in text
        assert "config_path" in text
