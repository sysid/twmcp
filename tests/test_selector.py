from unittest.mock import patch, MagicMock

import pytest

from twmcp.config import Server
from twmcp.selector import (
    parse_select_value,
    validate_server_names,
    select_servers_interactive,
)


class TestParseSelectValue:
    def test_single_name(self):
        assert parse_select_value("github") == ["github"]

    def test_comma_separated(self):
        assert parse_select_value("github,local-proxy") == ["github", "local-proxy"]

    def test_strips_whitespace(self):
        assert parse_select_value("github , local-proxy") == ["github", "local-proxy"]

    def test_filters_empty_segments(self):
        assert parse_select_value("github,,local-proxy") == ["github", "local-proxy"]

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="No server names"):
            parse_select_value("")

    def test_only_commas_raises(self):
        with pytest.raises(ValueError, match="No server names"):
            parse_select_value(",,,")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="No server names"):
            parse_select_value("  ,  ,  ")

    def test_none_keyword_returns_empty_list(self):
        assert parse_select_value("none") == []

    def test_none_mixed_with_names_raises(self):
        with pytest.raises(ValueError, match="reserved keyword"):
            parse_select_value("none,github")

    def test_none_case_sensitive(self):
        """'None' (capitalized) is NOT the reserved keyword — treated as a server name."""
        assert parse_select_value("None") == ["None"]

    def test_empty_string_error_suggests_none(self):
        with pytest.raises(ValueError, match="--select none"):
            parse_select_value("")


class TestValidateServerNames:
    @pytest.fixture
    def available(self):
        """Mimics CanonicalConfig.servers keys."""
        return {"github", "atlassian", "local-proxy"}

    def test_all_valid(self, available):
        result = validate_server_names(["github", "local-proxy"], available)
        assert result == ["github", "local-proxy"]

    def test_single_valid(self, available):
        result = validate_server_names(["atlassian"], available)
        assert result == ["atlassian"]

    def test_unknown_name_raises(self, available):
        with pytest.raises(ValueError, match="unknown-server"):
            validate_server_names(["unknown-server"], available)

    def test_unknown_name_lists_available(self, available):
        with pytest.raises(ValueError, match="atlassian"):
            validate_server_names(["unknown-server"], available)

    def test_mixed_valid_and_invalid_raises(self, available):
        with pytest.raises(ValueError, match="typo-server"):
            validate_server_names(["github", "typo-server"], available)

    def test_multiple_unknowns_reported(self, available):
        with pytest.raises(ValueError) as exc_info:
            validate_server_names(["bad1", "bad2"], available)
        assert "bad1" in str(exc_info.value)
        assert "bad2" in str(exc_info.value)


class TestSelectServersInteractive:
    """Tests for select_servers_interactive() with mocked TerminalMenu."""

    @pytest.fixture
    def servers(self):
        return {
            "github": Server(command="npx", type="stdio"),
            "atlassian": Server(type="http", url="https://example.com"),
            "local-proxy": Server(command="mcp-proxy", type="stdio"),
        }

    @patch("twmcp.selector.TerminalMenu")
    def test_all_selected_returns_all_names(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = (0, 1, 2)
        result = select_servers_interactive(servers)
        assert result == ["github", "atlassian", "local-proxy"]

    @patch("twmcp.selector.TerminalMenu")
    def test_subset_returns_subset(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = (0, 2)
        result = select_servers_interactive(servers)
        assert result == ["github", "local-proxy"]

    @patch("twmcp.selector.TerminalMenu")
    def test_cancel_returns_none(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = None
        mock_menu_cls.return_value.chosen_accept_key = None
        result = select_servers_interactive(servers)
        assert result is None

    @patch("twmcp.selector.TerminalMenu")
    def test_empty_selection_returns_empty_list(self, mock_menu_cls, servers):
        """Enter without Space-toggling → empty list (not first item)."""
        mock_menu_cls.return_value.show.return_value = None
        mock_menu_cls.return_value.chosen_accept_key = "enter"
        result = select_servers_interactive(servers)
        assert result == []

    @patch("twmcp.selector.TerminalMenu")
    def test_multi_select_does_not_auto_select_on_accept(self, mock_menu_cls, servers):
        """TerminalMenu must be created with multi_select_select_on_accept=False."""
        mock_menu_cls.return_value.show.return_value = (0,)
        mock_menu_cls.return_value.chosen_accept_key = "enter"
        select_servers_interactive(servers)
        call_kwargs = mock_menu_cls.call_args[1]
        assert call_kwargs["multi_select_select_on_accept"] is False
        assert call_kwargs["multi_select_empty_ok"] is True

    @patch("twmcp.selector.TerminalMenu")
    def test_labels_show_name_and_type(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = (0,)
        select_servers_interactive(servers)
        call_args = mock_menu_cls.call_args
        labels = call_args[0][0]
        assert "github [stdio]" in labels
        assert "atlassian [http]" in labels
        assert "local-proxy [stdio]" in labels

    @patch("twmcp.selector.TerminalMenu")
    def test_no_preselected_entries(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = (0,)
        select_servers_interactive(servers)
        call_kwargs = mock_menu_cls.call_args[1]
        assert "preselected_entries" not in call_kwargs

    @patch("twmcp.selector.TerminalMenu")
    def test_single_index_returns_as_list(self, mock_menu_cls, servers):
        """TerminalMenu returns int for single select in some modes."""
        mock_menu_cls.return_value.show.return_value = 1
        result = select_servers_interactive(servers)
        assert result == ["atlassian"]
