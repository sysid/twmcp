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
