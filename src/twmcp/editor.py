"""Editor resolution and config initialization for twmcp."""

import os
import shlex
import shutil
import subprocess
from pathlib import Path


def resolve_editor() -> tuple[str, list[str]]:
    """Resolve the user's preferred editor.

    Precedence: $EDITOR > $VISUAL > vi.
    Returns (command, extra_args) to support editors like "code --wait".
    """
    raw = os.environ.get("EDITOR", "") or os.environ.get("VISUAL", "") or "vi"
    parts = shlex.split(raw)
    return parts[0], parts[1:]


DEFAULT_CONFIG_TEMPLATE = """\
# twmcp canonical configuration
# See: https://github.com/sysid/twmcp
#
# Uncomment and edit the examples below, or add your own servers.

# Optional: load secrets from a dotenv file (relative to this config)
# env_file = "secrets.env"

[servers.example-stdio]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-example"]
type = "stdio"

# [servers.example-stdio.env]
# API_KEY = "${API_KEY}"

# [servers.example-http]
# type = "http"
# url = "https://example.com/mcp/"
#
# [servers.example-http.headers]
# Authorization = "Bearer ${AUTH_TOKEN}"
"""


def init_config(path: Path) -> None:
    """Create a new config file with sensible defaults.

    Creates parent directories as needed.
    Raises FileExistsError if the file already exists.
    """
    if path.exists():
        raise FileExistsError(f"Config file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEMPLATE)


def open_in_editor(path: Path) -> int:
    """Open a file in the user's preferred editor.

    Raises FileNotFoundError if the editor command is not found on PATH.
    Returns the editor's exit code.
    """
    cmd, extra_args = resolve_editor()
    if not shutil.which(cmd):
        raise FileNotFoundError(f"Editor not found: {cmd}")
    result = subprocess.run([cmd, *extra_args, str(path)])
    return result.returncode
