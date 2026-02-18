# Research: Edit Config Command

## R1: Editor Resolution Convention

**Decision**: Use `$EDITOR` > `$VISUAL` > `vi` precedence.

**Rationale**: This is the standard Unix convention. `$EDITOR` is the line editor variable (historically `ed`), `$VISUAL` is the full-screen editor (historically `vi`). Modern practice uses `$EDITOR` as the primary variable. `git`, `crontab -e`, `kubectl edit`, and `sudoedit` all follow this pattern.

**Alternatives considered**:
- `sensible-editor` (Debian-specific, not portable)
- `$VISUAL` first (less common in modern tools, would confuse users)
- `open` on macOS (opens GUI editor, wrong for CLI tool)
- No fallback (would require `$EDITOR` always set, poor UX)

## R2: Subprocess Strategy for Editor Launch

**Decision**: Use `subprocess.run([editor, str(path)])` with inherited stdio.

**Rationale**: The editor needs full terminal control (stdin, stdout, stderr). `subprocess.run` is the simplest correct approach — it blocks until the editor exits, returns the exit code, and handles signals properly (Ctrl+C, SIGTSTP).

**Alternatives considered**:
- `os.system(f"{editor} {path}")` — shell injection risk, deprecated pattern
- `os.execvp` — replaces the current process, no return to twmcp
- `subprocess.Popen` — unnecessary complexity for a blocking call

## R3: Overwrite Protection Strategy

**Decision**: Check `path.exists()` before writing. If exists, raise error.

**Rationale**: Simple existence check is sufficient. No need for file locking or atomic operations — this is a single-user CLI tool. The race window between check and write is irrelevant in this context.

**Alternatives considered**:
- `O_CREAT | O_EXCL` atomic open — overkill for CLI tool
- Interactive prompt "Overwrite? [y/N]" — spec explicitly says refuse, don't ask
- Backup existing file then write — adds complexity, spec says refuse

## R4: Default Template Content

**Decision**: Static string constant with TOML comments and commented-out examples.

**Rationale**: A static template is:
- Easy to test (string comparison)
- Easy to maintain (edit the string)
- Easy for users to understand (reads like documentation)

The template includes commented-out examples for both server types (stdio, http) so users can uncomment and modify. It does NOT include active server definitions that would fail without real credentials.

**Alternatives considered**:
- Generate from code (CanonicalConfig → TOML) — no `toml.dumps` in stdlib, would need tomli-w dependency
- External template file (data_files) — packaging complexity, harder to test
- Jinja template — new dependency, overkill

## R5: Editor Validation

**Decision**: Use `shutil.which(editor)` before launching subprocess.

**Rationale**: Provides a clear "editor not found" error instead of a cryptic `FileNotFoundError` from subprocess. `shutil.which` handles PATH lookup correctly. Only check the first word (the command), not the full string, to support `$EDITOR="code --wait"` patterns.

**Update**: Actually, `$EDITOR` can contain arguments (e.g., `code --wait`, `emacs -nw`). Need to split on whitespace to extract the command and additional args. Use `shlex.split()` for proper parsing, then validate only the first token with `shutil.which()`.
