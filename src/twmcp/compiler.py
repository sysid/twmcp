import json
import sys
from pathlib import Path

from twmcp.agents import AgentProfile
from twmcp.config import CanonicalConfig, Server


def _apply_override(server: Server, agent_name: str) -> Server:
    """Return a new Server with agent-specific overrides applied."""
    if agent_name not in server.overrides:
        return server

    ov = server.overrides[agent_name]
    return Server(
        command=ov.command if ov.command is not None else server.command,
        args=ov.args if ov.args is not None else server.args,
        type=ov.type if ov.type is not None else server.type,
        env=ov.env if ov.env is not None else server.env,
        url=ov.url if ov.url is not None else server.url,
        headers=ov.headers if ov.headers is not None else server.headers,
        tools=ov.tools if ov.tools is not None else server.tools,
    )


def _build_server_dict(server: Server, profile: AgentProfile) -> dict | None:
    """Build agent-specific dict for a single server.

    Returns None if the server should be skipped for this agent.
    """
    merged = _apply_override(server, profile.name)

    # Agents with header_style "none" don't support http/sse servers
    if merged.type in ("http", "sse") and profile.header_style == "none":
        return None

    result: dict = {}

    # Type field — omitted for header_style "none" (e.g. claude-desktop)
    if profile.header_style != "none":
        result["type"] = profile.type_mapping.get(merged.type, merged.type)

    # Stdio fields
    if merged.command:
        result["command"] = merged.command
    if merged.args:
        result["args"] = list(merged.args)

    # URL (http/sse)
    if merged.url:
        result["url"] = merged.url

    # Headers — style depends on agent profile
    if merged.headers:
        if profile.header_style == "flat":
            result["headers"] = dict(merged.headers)
        elif profile.header_style == "nested":
            result["requestInit"] = {"headers": dict(merged.headers)}

    # Tools filter
    if merged.tools is not None:
        result["tools"] = list(merged.tools)

    # Env vars
    if merged.env:
        result["env"] = dict(merged.env)

    return result


def transform_for_agent(config: CanonicalConfig, profile: AgentProfile) -> dict:
    """Transform canonical config into agent-specific JSON structure."""
    servers: dict = {}
    for name, server in config.servers.items():
        server_dict = _build_server_dict(server, profile)
        if server_dict is None:
            print(
                f"Warning: Skipping server '{name}' "
                f"(type '{server.type}' not supported by {profile.name})",
                file=sys.stderr,
            )
            continue
        servers[name] = server_dict

    return {profile.top_level_key: servers}


def write_config(compiled: dict, path: Path) -> None:
    """Write compiled config as JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(compiled, indent=2) + "\n")
