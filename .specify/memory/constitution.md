<!--
Sync Impact Report
===================
Version change: 1.1.1 → 1.2.0 (MINOR: add src/ layout, uv run pattern,
  fix directory layout, expand tooling guidance)
Modified principles: None (principles unchanged)
Added sections: None
Removed sections: None
Modified sections:
  - Technical Constraints > Tooling: added uv run Makefile pattern,
    clarified environment management
  - Technical Constraints > Testing: updated test execution to uv run
  - Technical Constraints > Directory Layout: fixed to src/ layout
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ already uses src/ as default
  - .specify/templates/spec-template.md ✅ no changes needed
  - .specify/templates/tasks-template.md ✅ already uses src/ paths
  - .specify/templates/checklist-template.md ✅ no changes needed
  - .specify/templates/agent-file-template.md ✅ no changes needed
Follow-up TODOs: None
-->

# twmcp Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

TDD rules from `~/.claude/CLAUDE.md` apply without exception.
This project adds no overrides to the global testing discipline.

### II. Simplicity

YAGNI and minimal-change rules from `~/.claude/CLAUDE.md` apply
without exception. This project adds no overrides.

### III. CLI Interface

- Text in/out protocol: arguments and stdin for input, stdout for
  output, stderr for errors.
- Support both human-readable and structured (JSON) output formats.
- Fail fast with meaningful error messages and non-zero exit codes.
- CLI MUST be independently testable via subprocess invocation.

**Rationale**: A CLI tool's value is its interface contract. Predictable
I/O behavior enables composition, scripting, and automated testing.

## Technical Constraints

### Runtime

- **Python version**: 3.13+ REQUIRED. No compatibility shims for older
  versions.
- **Dependencies**: Prefer stdlib. External dependencies MUST be
  justified.
- **Error handling**: Fail fast and explicitly. Specific exception types
  with meaningful messages.
- **Logging**: Structured logging to stderr. MUST NOT log sensitive
  data.

### Tooling

- **Formatter/Linter**: ruff (line-length 88, double quotes,
  indent-width 4, target py313).
- **Type checking**: ty.
- **Pre-commit hooks**: ruff-format, ruff (with `--fix`), ty.
- **Build backend**: setuptools via pyproject.toml.
- **Makefile**: All Python/tool invocations in Makefile MUST use
  `uv run` prefix (e.g. `uv run python -m pytest`,
  `uv run ruff check`, `uv run pre-commit run`). This ensures the
  correct virtualenv is used regardless of `.envrc` activation state.
- **Environment management**: uv manages the virtualenv at `.venv/`.
  `.envrc` is rsenv-managed and gitignored — do NOT modify it.
- **Version management**: bump-my-version with `VERSION` file as single
  source of truth. Tag format: `v{new_version}`.

### Testing

- **Framework**: pytest with markers `integration` (docker-based) and
  `experimentation` (not run in CI).
- **Coverage**: 85% minimum (`fail_under = 85`).
- **Async**: pytest-asyncio with `asyncio_mode = "auto"`.
- **Test execution**: `uv run python -m pytest -m "not (integration or
  experimentation)"` for unit tests.

### Directory Layout

```
twmcp/
  VERSION
  Makefile
  pyproject.toml
  .pre-commit-config.yaml
  .gitignore
  src/
    twmcp/
      __init__.py           # contains __version__
  tests/
    conftest.py
    test_*.py
    fixtures/
    integration/            # docker-based, @pytest.mark.integration
    experimentation/        # non-CI, @pytest.mark.experimentation
  scripts/
  .github/
    workflows/build.yml
    dependabot.yml
```

**Key**: This project uses the `src/` layout. Source code lives under
`src/twmcp/`, NOT at the repository root. The `[tool.setuptools
.packages.find]` section in pyproject.toml MUST have `where = ["src"]`.

## Development Workflow

- **Commits**: Claude MAY commit in this project (overrides global
  CLAUDE.md "only Tom commits" rule). No Claude references in commit
  messages.
- All other development workflow rules defer to `~/.claude/CLAUDE.md`.

## Governance

- `~/.claude/CLAUDE.md` is the highest-priority authority. This
  constitution MUST NOT contradict it unless an explicit override is
  documented (as in the commits rule above).
- This constitution extends CLAUDE.md with project-specific constraints.
  It MUST NOT duplicate rules already defined there.
- Amendments MUST be documented with version bump, rationale, and
  migration plan if applicable.
- All code changes MUST verify compliance with these principles.
- Versioning follows semantic versioning: MAJOR for principle
  removals/redefinitions, MINOR for new principles/sections, PATCH for
  clarifications and wording fixes.

**Version**: 1.2.0 | **Ratified**: 2026-02-17 | **Last Amended**: 2026-02-18
