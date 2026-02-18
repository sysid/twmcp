# Quickstart: Edit Config Command

## What's changing

Adding `twmcp edit` command to open the canonical TOML config in the user's editor, with `--init` to bootstrap a new config.

## Implementation order (TDD)

### Step 1: editor.py — resolve_editor()

```bash
# Write test first
uv run python -m pytest tests/test_editor.py::TestResolveEditor -v
# Then implement in src/twmcp/editor.py
```

Tests: EDITOR set, VISUAL fallback, vi default, EDITOR with args (shlex split).

### Step 2: editor.py — DEFAULT_CONFIG_TEMPLATE + init_config()

```bash
uv run python -m pytest tests/test_editor.py::TestInitConfig -v
```

Tests: creates file, creates parent dirs, refuses overwrite (FileExistsError), template is valid TOML.

### Step 3: editor.py — open_in_editor()

```bash
uv run python -m pytest tests/test_editor.py::TestOpenInEditor -v
```

Tests: calls subprocess.run with correct args, returns exit code, handles missing editor.

### Step 4: cli.py — edit command

```bash
uv run python -m pytest tests/test_cli.py::TestEditCommand -v
```

Tests: edit opens editor, edit --init creates + opens, --init refuses overwrite, missing config suggests --init.

### Full test suite

```bash
make test
```
