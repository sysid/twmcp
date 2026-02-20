"""Server selection for the compile command.

Provides interactive multi-select prompt and non-interactive name
validation for the --select flag.
"""

import sys
from collections.abc import Set

from simple_term_menu import TerminalMenu

from twmcp.config import Server


_NONE_KEYWORD = "none"


def parse_select_value(value: str) -> list[str]:
    """Parse comma-separated server names from --select value.

    The keyword ``none`` (case-sensitive) is reserved: it returns an
    empty list, signalling that the caller should produce a config with
    zero servers.  ``none`` cannot be combined with other names.

    Raises ValueError if no valid names remain after parsing.
    """
    if value == _NONE_KEYWORD:
        return []

    names = [name.strip() for name in value.split(",") if name.strip()]
    if not names:
        raise ValueError(
            "No server names provided. Use --select none for empty configuration."
        )
    if _NONE_KEYWORD in names:
        raise ValueError(
            "'none' is a reserved keyword and cannot be combined with server names. "
            "Use --select none alone for empty configuration."
        )
    return names


def validate_server_names(names: list[str], available: Set[str]) -> list[str]:
    """Validate that all names exist in the available set.

    Raises ValueError listing unrecognized names and available options.
    """
    unknown = [n for n in names if n not in available]
    if unknown:
        available_str = ", ".join(sorted(available))
        unknown_str = ", ".join(f'"{n}"' for n in unknown)
        raise ValueError(
            f"Unknown server(s): {unknown_str}\n  Available: {available_str}"
        )
    return names


def is_interactive_terminal() -> bool:
    """Check if stdin is connected to an interactive terminal."""
    return sys.stdin.isatty()


def select_servers_interactive(
    servers: dict[str, Server],
) -> list[str] | None:
    """Show interactive multi-select prompt for MCP servers.

    Returns list of selected server names, empty list if none selected,
    or None if the user cancelled (Escape/Ctrl+C).
    """
    names = list(servers.keys())
    labels = [f"{name} [{servers[name].type}]" for name in names]

    menu = TerminalMenu(
        labels,
        multi_select=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        show_multi_select_hint=True,
        title="Select MCP servers (Space=toggle, Enter=confirm, Esc=cancel):",
    )
    chosen = menu.show()

    if chosen is None:
        # Both Escape and Enter-with-empty return None from show().
        # Distinguish via chosen_accept_key (set only on Enter).
        if menu.chosen_accept_key is not None:
            return []
        return None

    # TerminalMenu returns int for single selection, tuple for multi
    if isinstance(chosen, int):
        chosen = (chosen,)

    return [names[i] for i in chosen]
