<!--
Sync Impact Report
===================
Version change: 1.0.0 → 1.1.0 (MINOR: materially expanded Technical Constraints)
Modified principles: None
Added sections: None
Removed sections: None
Modified sections:
  - Technical Constraints: added Python tooling, testing, formatting,
    type checking, environment, versioning, build, and directory layout
    constraints derived from development-standards.md (sections 3, 6.2)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed
  - .specify/templates/spec-template.md ✅ no changes needed
  - .specify/templates/tasks-template.md ✅ no changes needed
  - .specify/templates/checklist-template.md ✅ no changes needed
  - .specify/templates/agent-file-template.md ✅ no changes needed
Follow-up TODOs: None
-->

# twmcp Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

- TDD is mandatory: write tests FIRST, verify they FAIL, then implement.
- Red-Green-Refactor cycle MUST be strictly enforced.
- ALL test failures MUST be investigated and resolved — never ignored
  or deleted.
- New functionality and bug fixes MUST include tests.
- Tests MUST focus on business logic and edge cases, not implementation
  details.

**Rationale**: Tests are the only reliable proof that code works.
Writing them first forces clear thinking about requirements before
implementation.

### II. Simplicity

- YAGNI: do not add features not needed now.
- Make the SMALLEST reasonable changes to achieve the outcome.
- Simple solutions over clever ones — always.
- No backward compatibility without explicit approval.
- No abstractions for one-time operations; three similar lines beat a
  premature abstraction.

**Rationale**: Complexity is the primary enemy of maintainable
software. Every unnecessary abstraction is a future maintenance burden.

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
- **Environment management**: uv via `layout_uv` in `.envrc`.
- **Version management**: bump-my-version with `VERSION` file as single
  source of truth. Tag format: `v{new_version}`.

### Testing

- **Framework**: pytest with markers `integration` (docker-based) and
  `experimentation` (not run in CI).
- **Coverage**: 85% minimum (`fail_under = 85`).
- **Async**: pytest-asyncio with `asyncio_mode = "auto"`.
- **Test execution**: `python -m pytest -m "not (integration or
  experimentation)"` for unit tests.

### Directory Layout

```
twmcp/
  VERSION
  Makefile
  pyproject.toml
  .pre-commit-config.yaml
  twmcp/
    __init__.py           # contains __version__
  tests/
    __init__.py
    conftest.py
    test_*.py
    integration/          # docker-based, @pytest.mark.integration
    experimentation/      # non-CI, @pytest.mark.experimentation
  scripts/
  .github/
    workflows/build.yml
    dependabot.yml
```

## Development Workflow

- **Commits**: Only Tom commits. No Claude references in commit
  messages.
- **Code changes**: SMALLEST reasonable changes. Match surrounding code
  style.
- **Bugs**: Fix immediately when found. Find root cause — never fix
  symptoms.
- **Documentation**: Comments explain WHY, not WHAT. Docs MUST reflect
  changes.

## Governance

- This constitution supersedes all other development practices for this
  project.
- Amendments MUST be documented with version bump, rationale, and
  migration plan if applicable.
- All code changes MUST verify compliance with these principles.
- Complexity MUST be justified against the Simplicity principle.
- Versioning follows semantic versioning: MAJOR for principle
  removals/redefinitions, MINOR for new principles/sections, PATCH for
  clarifications and wording fixes.
- Use CLAUDE.md for runtime development guidance.

**Version**: 1.1.0 | **Ratified**: 2026-02-17 | **Last Amended**: 2026-02-17
