# Research: Simplify Select Options

**Feature**: 005-simplify-select
**Date**: 2026-02-20

## R-001: Typer Option[str] behavior with empty strings

- **Decision**: `--select ""` passes empty string to the callback. Typer/Click does not strip it.
- **Rationale**: Verified in existing codebase — `parse_select_value("")` currently raises `ValueError`. We keep this behavior and enhance the error message to suggest `--select none`.
- **Alternatives considered**: Making `--select` a `flag_value` option again (rejected: that's what we're removing).

## R-002: Reserved keyword approach for empty selection

- **Decision**: `none` (case-sensitive) is a reserved keyword in `parse_select_value`.
- **Rationale**: Shell-safe, explicit, readable. Clarified during `/speckit.clarify` session.
- **Alternatives considered**: `--select ""` (shell-fragile), `--no-servers` flag (too many flags).

## R-003: Removal scope for monkey-patch infrastructure

- **Decision**: Remove `_INTERACTIVE` sentinel, `_apply_select_patch()`, `_install_select_patch()`, module-level `_install_select_patch()` call, and `import click`.
- **Rationale**: All patch code becomes dead once `--interactive` is a separate flag. The `click` import was only used for monkey-patching.
- **Alternatives considered**: Keeping `click` import "just in case" (rejected: YAGNI).

## Summary

No unknowns remain. All decisions were resolved during the `/speckit.clarify` phase. This is a straightforward refactoring with no external dependencies or technology choices to research.
