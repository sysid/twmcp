import json
import logging
from pathlib import Path
from typing import Optional

import click
import typer

from twmcp import __version__
from twmcp.agents import get_profile, list_agents, AGENT_REGISTRY
from twmcp.compiler import transform_for_agent, write_config
from twmcp.config import CanonicalConfig, load_and_resolve
from twmcp.extractor import extract_from_file
from twmcp.selector import (
    is_interactive_terminal,
    parse_select_value,
    select_servers_interactive,
    validate_server_names,
)

# Sentinel value for bare --select (interactive mode)
_INTERACTIVE = "__interactive__"

logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=True)

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
    select: Optional[str] = typer.Option(
        None,
        "--select",
        help="Select servers: bare for interactive, comma-separated for filter",
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
    canonical = _resolve_selection(select, canonical)

    if all_agents:
        _compile_all(canonical, dry_run)
    else:
        assert agent is not None  # guarded by the check above
        _compile_single(agent, canonical, dry_run)


def _resolve_selection(
    select: str | None, canonical: CanonicalConfig
) -> CanonicalConfig:
    """Apply --select filtering to canonical config.

    Returns the original config if select is None, or a filtered copy
    containing only the selected servers.
    """
    if select is None:
        return canonical

    if select == _INTERACTIVE:
        if not is_interactive_terminal():
            typer.echo(
                "Error: --select requires an interactive terminal.\n"
                "  Use --select <names> for non-interactive mode.",
            )
            raise typer.Exit(1)

        selected = select_servers_interactive(canonical.servers)
        if selected is None:
            raise typer.Exit(0)
        if not selected:
            typer.echo("No servers selected.")
            raise typer.Exit(0)
    else:
        try:
            names = parse_select_value(select)
        except ValueError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(1)
        try:
            selected = validate_server_names(
                names, set(canonical.servers.keys())
            )
        except ValueError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(1)

    filtered = {k: v for k, v in canonical.servers.items() if k in selected}
    return CanonicalConfig(servers=filtered, env_file=canonical.env_file)


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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "-v", "--verbose", help="verbosity"),
    version: bool = typer.Option(False, "-V", "--version", help="show version"),
):
    log_fmt = r"%(asctime)-15s %(levelname)-7s %(message)s"
    logging.basicConfig(
        format=log_fmt,
        level=logging.DEBUG if verbose else logging.INFO,
        datefmt="%m-%d %H:%M:%S",
        force=True,
    )
    if ctx.invoked_subcommand is None and version:
        ctx.invoke(print_version)
    if ctx.invoked_subcommand is None and not version:
        typer.echo(ctx.get_help())


@app.command("version", help="Show version", hidden=True)
def print_version() -> None:
    typer.echo(f"twmcp version: {__version__}")


def _apply_select_patch(click_cmd: click.Command) -> None:
    """Apply the optional-value patch to --select on a Click command."""
    cmd = (
        click_cmd.commands.get("compile")
        if isinstance(click_cmd, click.Group)
        else click_cmd
    )
    if cmd is None:
        return
    for param in cmd.params:
        if isinstance(param, click.Option) and param.name == "select":
            param._flag_needs_value = True
            param.flag_value = _INTERACTIVE
            return


def _install_select_patch() -> None:
    """Monkey-patch typer.main.get_command to apply the --select patch.

    Typer recreates Click commands on every get_command() call, so a
    one-time patch gets lost. This wraps get_command to reapply the
    patch each time a fresh Click command tree is built.

    Workaround for Click #3084 regression and Typer's removal of
    flag_value. Can be removed when Click ships the fix.
    """
    original = typer.main.get_command

    def _patched_get_command(typer_app: typer.Typer) -> click.Command:
        click_app = original(typer_app)
        if typer_app is app:
            _apply_select_patch(click_app)
        return click_app

    typer.main.get_command = _patched_get_command  # type: ignore[assignment]

    # Typer's CliRunner (typer/testing.py) imports get_command at module
    # level as a local alias (_get_command). Without patching that reference
    # too, runner.invoke() in tests bypasses our patch entirely.
    try:
        from typer import testing as _typer_testing

        _typer_testing._get_command = _patched_get_command  # type: ignore[attr-defined]
    except (ImportError, AttributeError):
        pass  # testing module not available or internal name changed


_install_select_patch()
