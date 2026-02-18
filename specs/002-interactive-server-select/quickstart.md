# Quickstart: Interactive Server Selection

**Feature**: 002-interactive-server-select
**Date**: 2026-02-18

## What Changed

The `twmcp compile` command gains a `--select` flag that lets you choose which MCP servers to include in the compiled output.

## Usage

### Interactive mode (pick from a menu)

```bash
twmcp compile copilot-cli --select
```

A multi-select prompt appears with all servers pre-checked. Use Space to toggle, Enter to confirm, Escape to cancel.

### Non-interactive mode (specify by name)

```bash
twmcp compile copilot-cli --select github,local-proxy
```

Compiles only the named servers. Useful in scripts and aliases.

### Compile all agents with selection

```bash
twmcp compile --all --select              # interactive
twmcp compile --all --select github       # non-interactive
```

The selection is applied to every agent (incompatible servers are still skipped per agent rules).

### Existing behavior (no change)

```bash
twmcp compile copilot-cli                 # all servers, as before
twmcp compile --all                       # all servers, all agents, as before
```

## New Dependency

- `simple-term-menu` — zero-dependency package for the terminal multi-select prompt

## Files Modified

| File | Change |
|------|--------|
| `src/twmcp/cli.py` | Add `--select` option + Click patch, selection logic |
| `src/twmcp/selector.py` | New module: interactive prompt + name validation |
| `pyproject.toml` | Add `simple-term-menu` dependency |
| `tests/test_cli.py` | Tests for `--select` modes |
| `tests/test_selector.py` | Tests for selection logic |
