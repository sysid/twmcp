"""Server selection for the compile command.

Provides interactive multi-select prompt and non-interactive name
validation for the --select flag.
"""

import logging
import sys
from collections.abc import Set
from typing import TYPE_CHECKING

from simple_term_menu import TerminalMenu

from twmcp.config import Server

if TYPE_CHECKING:
    from twmcp.config import CanonicalConfig

logger = logging.getLogger(__name__)


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


def resolve_profile_servers(name: str, canonical: "CanonicalConfig") -> set[str]:
    """Resolve a profile name to its set of server names.

    Validates that ``name`` exists in ``canonical.profiles`` and that
    every referenced server exists in ``canonical.servers``. Duplicates
    in the profile list are deduplicated by set semantics.
    """
    if name not in canonical.profiles:
        if not canonical.profiles:
            raise ValueError(
                f'No profiles defined in config. Cannot resolve --profile "{name}".\n'
                f"  Add a [profiles] table to the config to define profiles."
            )
        available = ", ".join(sorted(canonical.profiles))
        raise ValueError(
            f'Unknown profile "{name}".\n'
            f"  Available profiles: {available}\n"
            f"  Run 'twmcp profiles' to see all defined profiles."
        )

    members = canonical.profiles[name]
    server_keys = set(canonical.servers)
    missing = sorted({m for m in members if m not in server_keys})
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(
            f'Profile "{name}" references unknown server(s): {missing_str}\n'
            f"  Fix the profile definition or add the server(s) under [servers]."
        )

    resolved = set(members)
    excluded = sorted(server_keys - resolved)
    logger.debug(
        "profile %r: resolved to %d server(s): %s",
        name,
        len(resolved),
        sorted(resolved),
    )
    logger.debug(
        "profile %r: excluded %d server(s) not in profile: %s",
        name,
        len(excluded),
        excluded,
    )
    return resolved


def is_interactive_terminal() -> bool:
    """Check if stdin is connected to an interactive terminal."""
    return sys.stdin.isatty()


def select_servers_interactive(
    servers: dict[str, Server],
    preselected: "Set[str] | None" = None,
) -> list[str] | None:
    """Show interactive multi-select prompt for MCP servers.

    ``preselected`` is an optional iterable of server names that will be
    pre-checked in the menu (used by ``--profile <name> --interactive``).
    Names not present in ``servers`` are silently dropped.

    Returns list of selected server names, empty list if none selected,
    or None if the user cancelled (Escape/Ctrl+C).
    """
    names = list(servers.keys())
    labels = [f"{name} [{servers[name].type}]" for name in names]

    preselected_labels: list[str] | None = None
    if preselected:
        preselected_labels = [
            f"{n} [{servers[n].type}]" for n in names if n in preselected
        ]

    menu = TerminalMenu(
        labels,
        multi_select=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        show_multi_select_hint=True,
        title="Select MCP servers (Space=toggle, Enter=confirm, Esc=cancel):",
        preselected_entries=preselected_labels,
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
