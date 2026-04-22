from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AgentProfile:
    name: str
    config_path: Path
    top_level_key: str
    type_mapping: dict[str, str] = field(default_factory=dict)
    header_style: str = "flat"  # "flat", "nested", "none"


AGENT_REGISTRY: dict[str, AgentProfile] = {
    "copilot-cli": AgentProfile(
        name="copilot-cli",
        config_path=Path(".copilot") / "mcp-config.json",
        top_level_key="mcpServers",
        type_mapping={"stdio": "local"},
        header_style="flat",
    ),
    "intellij": AgentProfile(
        name="intellij",
        config_path=(
            Path.home() / ".config" / "github-copilot" / "intellij" / "mcp.json"
        ),
        top_level_key="servers",
        type_mapping={},
        header_style="nested",
    ),
    "claude-code": AgentProfile(
        name="claude-code",
        config_path=Path(".claude") / "mcp-config.json",
        top_level_key="mcpServers",
        type_mapping={},
        header_style="flat",
    ),
    "claude-desktop": AgentProfile(
        name="claude-desktop",
        config_path=(
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        ),
        top_level_key="mcpServers",
        type_mapping={},
        header_style="none",
    ),
}


def get_profile(name: str) -> AgentProfile:
    try:
        return AGENT_REGISTRY[name]
    except KeyError:
        available = ", ".join(sorted(AGENT_REGISTRY))
        raise KeyError(f"Unknown agent: {name!r}. Available: {available}") from None


def list_agents() -> list[AgentProfile]:
    return list(AGENT_REGISTRY.values())


def resolve_profile(name: str, overrides: dict[str, str]) -> AgentProfile:
    """Return the profile for ``name`` with its ``config_path`` replaced by the
    override if one exists in ``overrides``. Applies ``~`` expansion.

    Raises KeyError for unknown agent names (via get_profile).
    """
    base = get_profile(name)
    override = overrides.get(name)
    if override is None:
        return base
    # AgentProfile is frozen — use dataclasses.replace-like pattern via constructor.
    return AgentProfile(
        name=base.name,
        config_path=Path(override).expanduser(),
        top_level_key=base.top_level_key,
        type_mapping=base.type_mapping,
        header_style=base.header_style,
    )
