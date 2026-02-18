import json
from pathlib import Path
from typing import Optional

import typer

from twmcp.agents import get_profile, list_agents, AGENT_REGISTRY
from twmcp.compiler import transform_for_agent, write_config
from twmcp.config import load_and_resolve
from twmcp.extractor import extract_from_file

app = typer.Typer(add_completion=False)

DEFAULT_CONFIG = Path.home() / ".config" / "twmcp" / "config.toml"


def _load_config_or_exit(config: Path):
    """Load and resolve config, handling errors with proper exit codes."""
    try:
        return load_and_resolve(config)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(
            f"Error: {e}\n"
            f"  Set these environment variables or add defaults: ${{VAR:-default}}",
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: Failed to load config\n  {e}")
        raise typer.Exit(1)


@app.command()
def compile(
    agent: Optional[str] = typer.Argument(
        None, help="Agent name (e.g. copilot-cli, intellij, claude-desktop)"
    ),
    all_agents: bool = typer.Option(
        False, "--all", help="Compile for all registered agents"
    ),
    config: Path = typer.Option(DEFAULT_CONFIG, help="Path to canonical config"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print compiled JSON to stdout, do not write files"
    ),
) -> None:
    """Compile canonical config for a specific agent or all agents."""
    if not agent and not all_agents:
        typer.echo(
            "Error: Specify an agent name or use --all\n"
            "  Run 'twmcp agents' to see all supported agents.",
        )
        raise typer.Exit(1)

    if agent and all_agents:
        typer.echo("Error: Cannot specify both an agent name and --all")
        raise typer.Exit(1)

    canonical = _load_config_or_exit(config)

    if all_agents:
        _compile_all(canonical, dry_run)
    else:
        assert agent is not None  # guarded by the check above
        _compile_single(agent, canonical, dry_run)


def _compile_single(agent: str, canonical, dry_run: bool) -> None:
    try:
        profile = get_profile(agent)
    except KeyError:
        available = ", ".join(sorted(AGENT_REGISTRY))
        typer.echo(
            f'Error: Unknown agent "{agent}"\n'
            f"  Available agents: {available}\n"
            f"  Run 'twmcp agents' to see all supported agents.",
        )
        raise typer.Exit(1)

    compiled = transform_for_agent(canonical, profile)

    if dry_run:
        typer.echo(json.dumps(compiled, indent=2))
    else:
        write_config(compiled, profile.config_path)
        typer.echo(f"Written: {profile.config_path}", err=True)


def _compile_all(canonical, dry_run: bool) -> None:
    errors: list[str] = []
    for profile in list_agents():
        compiled = transform_for_agent(canonical, profile)
        if dry_run:
            typer.echo(f"--- {profile.name} ---")
            typer.echo(json.dumps(compiled, indent=2))
        else:
            try:
                write_config(compiled, profile.config_path)
                typer.echo(f"Written: {profile.name} → {profile.config_path}", err=True)
            except Exception as e:
                errors.append(f"{profile.name}: {e}")
                typer.echo(f"Error: {profile.name}: {e}", err=True)

    if errors:
        raise typer.Exit(1)


@app.command()
def extract(
    mcp_json_file: Path = typer.Argument(help="Path to MCP JSON configuration file"),
) -> None:
    """Extract canonical TOML config from an MCP JSON file."""
    try:
        toml_output = extract_from_file(mcp_json_file)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(toml_output, nl=False)


@app.command()
def agents(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """List supported agents with config details."""
    if json_output:
        data = [
            {
                "name": a.name,
                "config_path": str(a.config_path),
                "top_level_key": a.top_level_key,
            }
            for a in list_agents()
        ]
        typer.echo(json.dumps(data, indent=2))
    else:
        # Simple table output
        typer.echo(f"{'Agent':<20s} {'Config Path':<50s} {'Key'}")
        typer.echo(f"{'-' * 20} {'-' * 50} {'-' * 15}")
        for a in list_agents():
            path_str = str(a.config_path).replace(str(Path.home()), "~")
            typer.echo(f"{a.name:<20s} {path_str:<50s} {a.top_level_key}")
