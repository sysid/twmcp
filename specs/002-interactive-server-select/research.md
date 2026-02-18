# Research: Interactive Server Selection

**Feature**: 002-interactive-server-select
**Date**: 2026-02-18

## Decision 1: Dual-Mode `--select` Flag in Typer

### Decision

Use a module-level monkey-patch of Click's `_flag_needs_value` attribute to enable optional-value behavior on the `--select` option.

### Rationale

Neither Typer 0.24.0 nor Click 8.3.1 natively supports the `is_flag=False, flag_value=` pattern needed for a dual-mode option:

- **Typer 0.24.0**: Removed `flag_value` and `is_flag` from its public API (deprecated in 0.15, removed later). `OptionInfo` no longer accepts these parameters.
- **Click 8.3.1**: Has a regression (#3084) where `is_flag=False, flag_value=` doesn't work. Fix merged Nov 2025 (PR #3152) but not yet released.

The monkey-patch sets `_flag_needs_value = True` and `flag_value = sentinel` on the Click `Option` object after Typer builds it. This is a ~10-line, well-contained workaround.

```
--select               → sentinel value ("__interactive__") → interactive mode
--select github,proxy  → "github,proxy"                     → non-interactive filter
(not passed)           → None                                → all servers (current behavior)
```

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Two separate flags (`--select` bool + `--servers` string) | Spec clarification chose dual-mode single flag. Two flags complicate UX. |
| Pure Click command (bypass Typer) | Loses Typer type hints, breaks consistency with existing `agents` command. |
| Custom Click `Option` subclass | More code, same private API dependency, harder to test. |
| Wait for Click 8.4.0 fix | Unreleased, unknown timeline. |

### Risk

- `_flag_needs_value` is a private Click attribute (prefixed `_`). Stable across Click 8.x but could change in 9.x.
- When Click ships the fix for #3084, the patch can be removed and replaced with native `is_flag=False, flag_value=`.
- Patch is documented with references to Click #3084 and Typer's removal of `flag_value`.

---

## Decision 2: Interactive Multi-Select Library

### Decision

Use `simple-term-menu` for the interactive multi-select prompt.

### Rationale

| Criterion | simple-term-menu | questionary | InquirerPy | DIY with Rich |
|-----------|-----------------|-------------|------------|---------------|
| Dependencies | **Zero** | prompt_toolkit + wcwidth | prompt_toolkit + wcwidth | ~100 LOC manual |
| Package size | 27.6 KB | 36.8 KB + 391 KB prompt_toolkit | 67.7 KB + 391 KB | N/A |
| Pre-selected items | `preselected_entries` | `Choice(checked=True)` | `enabled=True` | Manual |
| Ctrl+C handling | Returns `None` | Returns `None` | Configurable | Manual try/except |
| macOS support | Yes | Yes | Yes | Yes |
| Maintenance | Active (Dec 2024) | Active (Aug 2025) | **Abandoned** (Jun 2022) | N/A |

`simple-term-menu` aligns best with the constitution's "Prefer stdlib. External dependencies MUST be justified":
- Zero transitive dependencies — it IS basically stdlib
- Single-file implementation, easy to vendor if abandoned
- Does exactly multi-select, nothing more (YAGNI)

### Dependency Justification

Zero-dependency single-file package providing terminal multi-select UI. No stdlib equivalent exists. Alternatives require prompt_toolkit (391 KB + transitive deps) or ~100 LOC of fragile raw terminal code.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| `questionary` | Pulls in prompt_toolkit (391 KB + wcwidth). Overkill for a single prompt. |
| `InquirerPy` | Abandoned since Jun 2022. Adding unmaintained dep is a liability. |
| DIY with Rich | ~100 LOC of raw terminal manipulation. Violates YAGNI and "simple over clever." |

---

## Decision 3: Server Filtering Architecture

### Decision

Implement server filtering as a simple name-set applied to `CanonicalConfig.servers` before passing to `transform_for_agent`. No new data structures or abstractions needed.

### Rationale

The selection is a transient per-invocation concept (per spec). The simplest approach is:

1. Load canonical config (existing)
2. If `--select` active: filter `config.servers` dict by selected names
3. Pass filtered config to existing `transform_for_agent` (unchanged)

This requires no changes to `config.py`, `compiler.py`, or `agents.py`. All changes are contained in `cli.py` plus a new `selector.py` module for the interactive prompt logic.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Add selection to `CanonicalConfig` dataclass | Over-engineering. Selection is transient, not part of config. |
| Filter inside `transform_for_agent` | Mixes concerns. Compiler shouldn't know about UI selections. |
| Add a `ServerFilter` class | Premature abstraction for a simple name-set operation. |
