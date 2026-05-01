import logging
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from twmcp.agents import AGENT_REGISTRY
from twmcp.interpolate import find_unresolved, load_dotenv, resolve_variables

logger = logging.getLogger(__name__)


@dataclass
class PartialServer:
    """Agent-specific override for a server. Only set fields are applied."""

    command: str | None = None
    args: list[str] | None = None
    type: str | None = None
    env: dict[str, str] | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    tools: list[str] | None = None


@dataclass
class Server:
    command: str = ""
    args: list[str] = field(default_factory=list)
    type: str = "stdio"
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    tools: list[str] | None = None
    overrides: dict[str, PartialServer] = field(default_factory=dict)


@dataclass
class CanonicalConfig:
    servers: dict[str, Server]
    env_file: str | None = None
    agent_overrides: dict[str, str] = field(default_factory=dict)
    profiles: dict[str, list[str]] = field(default_factory=dict)


def _parse_server(name: str, data: dict) -> Server:
    overrides_raw = data.pop("overrides", {})
    overrides = {}
    for agent_name, override_data in overrides_raw.items():
        overrides[agent_name] = PartialServer(**override_data)

    return Server(
        command=data.get("command", ""),
        args=data.get("args", []),
        type=data.get("type", "stdio"),
        env=data.get("env", {}),
        url=data.get("url"),
        headers=data.get("headers", {}),
        tools=data.get("tools"),
        overrides=overrides,
    )


def _load_raw(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "rb") as f:
        return tomllib.load(f)


def _parse_agent_overrides(raw: dict) -> dict[str, str]:
    """Parse `[agents.<name>]` sections. Validate names against AGENT_REGISTRY
    and `config_path` values as strings. Empty sections are silently ignored.
    """
    agents_raw = raw.get("agents") or {}
    if not isinstance(agents_raw, dict):
        raise ValueError(f"[agents] must be a table, got {type(agents_raw).__name__}")

    overrides: dict[str, str] = {}
    valid = sorted(AGENT_REGISTRY)
    for name, section in agents_raw.items():
        if name not in AGENT_REGISTRY:
            raise ValueError(
                f'Unknown agent "{name}" in [agents.*]. '
                f"Valid agents: {', '.join(valid)}"
            )
        if not isinstance(section, dict):
            raise ValueError(
                f"[agents.{name}] must be a table, got {type(section).__name__}"
            )
        config_path = section.get("config_path")
        if config_path is None:
            continue
        if not isinstance(config_path, str):
            raise ValueError(
                f"[agents.{name}].config_path must be a string, "
                f"got {type(config_path).__name__}"
            )
        overrides[name] = config_path
        logger.debug("[agents.%s] config_path override parsed: %r", name, config_path)
    if not overrides:
        logger.debug("no [agents.*] config_path overrides found in config")
    return overrides


def _parse_profiles(raw: dict) -> dict[str, list[str]]:
    """Parse `[profiles]` section. Validate types only — server-name
    references are checked at compile time so a stale profile does not
    break unrelated commands.
    """
    profiles_raw = raw.get("profiles")
    if profiles_raw is None:
        logger.debug("no [profiles] section found in config")
        return {}
    if not isinstance(profiles_raw, dict):
        raise ValueError(
            f"[profiles] must be a table, got {type(profiles_raw).__name__}"
        )

    profiles: dict[str, list[str]] = {}
    for name, value in profiles_raw.items():
        if not isinstance(value, list):
            raise ValueError(
                f"[profiles].{name} must be a list of server names, "
                f"got {type(value).__name__}"
            )
        for i, entry in enumerate(value):
            if not isinstance(entry, str):
                raise ValueError(
                    f"[profiles].{name}[{i}] must be a string, "
                    f"got {type(entry).__name__}"
                )
        profiles[name] = list(value)
        logger.debug("[profiles].%s parsed: %d server(s)", name, len(value))
    return profiles


def _parse_raw(raw: dict, path: Path) -> CanonicalConfig:
    servers_raw = raw.get("servers")
    if not servers_raw:
        raise ValueError(f"No servers defined in {path}")

    servers = {}
    for name, data in servers_raw.items():
        servers[name] = _parse_server(name, dict(data))

    return CanonicalConfig(
        servers=servers,
        env_file=raw.get("env_file"),
        agent_overrides=_parse_agent_overrides(raw),
        profiles=_parse_profiles(raw),
    )


def _collect_unresolved(value: object, variables: dict[str, str]) -> list[str]:
    """Recursively find all unresolved variable names in a nested structure."""
    if isinstance(value, str):
        return find_unresolved(value, variables)
    if isinstance(value, dict):
        result: list[str] = []
        for v in value.values():
            result.extend(_collect_unresolved(v, variables))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_collect_unresolved(item, variables))
        return result
    return []


def _resolve_value(value: object, variables: dict[str, str]) -> object:
    """Recursively resolve ${VAR} placeholders in nested dicts/lists/strings."""
    if isinstance(value, str):
        return resolve_variables(value, variables)
    if isinstance(value, dict):
        return {k: _resolve_value(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item, variables) for item in value]
    return value


def _build_variables(raw: dict, config_dir: Path) -> dict[str, str]:
    """Build variable map from dotenv + os.environ (env wins)."""
    variables: dict[str, str] = {}
    env_file = raw.get("env_file")
    if env_file:
        dotenv_path = config_dir / env_file
        dotenv_vars = load_dotenv(dotenv_path)
        logger.debug(
            "loaded %d variables from env_file=%s", len(dotenv_vars), dotenv_path
        )
        variables.update(dotenv_vars)
    else:
        logger.debug("no env_file declared in config")
    variables.update(os.environ)
    return variables


def load_config(path: Path) -> CanonicalConfig:
    """Load and parse config without variable interpolation."""
    return _parse_raw(_load_raw(path), path)


def load_and_resolve(path: Path) -> CanonicalConfig:
    """Load config with ${VAR} and ${VAR:-default} interpolation."""
    logger.debug("loading config from %s", path)
    raw = _load_raw(path)
    variables = _build_variables(raw, path.parent)

    # Pre-scan: collect ALL unresolved variables before raising
    missing = _collect_unresolved(raw, variables)
    if missing:
        var_list = ", ".join(sorted(set(missing)))
        raise ValueError(f"Unresolved variables: {var_list}")

    resolved = _resolve_value(raw, variables)
    assert isinstance(
        resolved, dict
    )  # raw was dict, _resolve_value preserves structure
    cfg = _parse_raw(resolved, path)
    logger.debug(
        "config loaded: %d server(s), %d agent override(s), %d profile(s)",
        len(cfg.servers),
        len(cfg.agent_overrides),
        len(cfg.profiles),
    )
    return cfg
