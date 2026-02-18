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
        config_path=Path.home() / ".copilot" / "mcp-config.json",
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
