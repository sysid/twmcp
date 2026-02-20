# Quickstart: 005-simplify-select

## What Changed

The `--select` flag on `twmcp compile` is simplified:

- **`--select <names>`** — Non-interactive. Comma-separated server names.
- **`--select none`** — Non-interactive. Produces empty configuration (zero servers).
- **`--interactive`** — New flag. Opens terminal multi-select menu.
- `--select` and `--interactive` are mutually exclusive.

## Before (old)

```bash
# Interactive (bare --select, relied on Click monkey-patch)
twmcp compile copilot-cli --select --dry-run

# Non-interactive filter
twmcp compile copilot-cli --select github,local-proxy --dry-run

# Empty selection — NOT POSSIBLE
```

## After (new)

```bash
# Interactive (dedicated flag)
twmcp compile copilot-cli --interactive --dry-run

# Non-interactive filter (unchanged)
twmcp compile copilot-cli --select github,local-proxy --dry-run

# Empty selection (new capability)
twmcp compile copilot-cli --select none --dry-run
```

## Development

```bash
# Run tests
make test

# Run specific test class
uv run python -m pytest tests/test_cli.py::TestCompileSelectNone -v
uv run python -m pytest tests/test_selector.py::TestParseSelectValue -v

# Verify no monkey-patch code remains
grep -r "_flag_needs_value\|_apply_select_patch\|_install_select_patch" src/
# Should return nothing
```
