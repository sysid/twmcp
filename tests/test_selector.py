from unittest.mock import patch

import pytest

from twmcp.config import CanonicalConfig, Server
from twmcp.selector import (
    parse_select_value,
    resolve_profile_servers,
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
    def test_no_preselected_entries_when_none_passed(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = (0,)
        select_servers_interactive(servers)
        call_kwargs = mock_menu_cls.call_args[1]
        # When preselected is None, the menu should not receive preselected_entries
        assert call_kwargs.get("preselected_entries") in (None, [])

    @patch("twmcp.selector.TerminalMenu")
    def test_preselected_forwarded_to_menu(self, mock_menu_cls, servers):
        mock_menu_cls.return_value.show.return_value = (0,)
        select_servers_interactive(servers, preselected={"github", "atlassian"})
        call_kwargs = mock_menu_cls.call_args[1]
        # Labels are "name [type]"; preselected_entries must use the same label form
        assert set(call_kwargs["preselected_entries"]) == {
            "github [stdio]",
            "atlassian [http]",
        }

    @patch("twmcp.selector.TerminalMenu")
    def test_single_index_returns_as_list(self, mock_menu_cls, servers):
        """TerminalMenu returns int for single select in some modes."""
        mock_menu_cls.return_value.show.return_value = 1
        result = select_servers_interactive(servers)
        assert result == ["atlassian"]


class TestResolveProfile:
    @pytest.fixture
    def cfg(self):
        return CanonicalConfig(
            servers={
                "server-a": Server(command="echo", args=["a"]),
                "server-b": Server(command="echo", args=["b"]),
                "server-c": Server(command="echo", args=["c"]),
            },
            profiles={
                "emea": ["server-a", "server-b"],
                "apac": ["server-c"],
                "empty": [],
                "dup": ["server-a", "server-a"],
                "bad": ["server-x", "server-y"],
            },
        )

    def test_unknown_profile_no_profiles_defined(self):
        cfg = CanonicalConfig(servers={"s": Server()}, profiles={})
        with pytest.raises(ValueError) as exc:
            resolve_profile_servers("emea", cfg)
        assert "No profiles defined" in str(exc.value)

    def test_unknown_profile_lists_available_sorted(self, cfg):
        with pytest.raises(ValueError) as exc:
            resolve_profile_servers("nope", cfg)
        msg = str(exc.value)
        assert "Unknown profile" in msg
        assert "nope" in msg
        # available list sorted
        avail_idx = msg.index("apac")
        assert (
            msg.index("apac")
            < msg.index("bad")
            < msg.index("dup")
            < msg.index("emea")
            < msg.index("empty")
        )

    def test_profile_references_missing_servers(self, cfg):
        with pytest.raises(ValueError) as exc:
            resolve_profile_servers("bad", cfg)
        msg = str(exc.value)
        assert "bad" in msg
        assert "server-x" in msg
        assert "server-y" in msg

    def test_valid_profile_returns_set(self, cfg):
        result = resolve_profile_servers("emea", cfg)
        assert result == {"server-a", "server-b"}

    def test_empty_profile_returns_empty_set(self, cfg):
        result = resolve_profile_servers("empty", cfg)
        assert result == set()

    def test_duplicates_deduplicated(self, cfg):
        result = resolve_profile_servers("dup", cfg)
        assert result == {"server-a"}
