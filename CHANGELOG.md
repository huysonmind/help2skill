# Changelog

All notable changes are listed here. The generated Markdown format is part of the
public interface: any change to it is called out under **Output**.

## Unreleased
- Fixed: the order of "Shared options" depended on Python's hash seed, so
  `help2skill check` could report a fresh file as stale (**Output**: the order is now
  the order options first appear).
- `check` prints the regenerate command shell-quoted, with `--app-dir` and
  `--resolve` when they were given.
- Machine-path warning also catches paths inside the running environment, the temp
  directory, and paths containing the user name.
- help2skill ships its own `SKILL.md` (`.agents/skills/help2skill/`).
- `examples/`: a Typer app, sqlite-utils and pipx; README demo and pre-commit recipe.

## 0.1.0 (2026-11-07)
- Introspect Click, Typer (including Typer ≥ 0.26 with vendored Click) and argparse
  into one model.
- `render_markdown`, `render_skill` (Agent Skills frontmatter validation).
- `--llms` flag: Click decorator, `add_llms_option`, Typer `LlmsOption` and
  `help2skill.typer.command`.
- Drift check: stale generated block, unknown subcommands/options and options at the
  wrong level in hand-written examples; default-command groups.
- `help2skill` command (`markdown`, `skill`, `check`) and
  `help2skill.testing.assert_skill_in_sync`.
- Large CLIs: `--llms` falls back to an index above 20,000 characters
  (`HELP2SKILL_LLMS_MAX_CHARS`); `SKILL.md` splits the full reference into
  `references/commands.md` above 30,000 characters (`--max-chars`).
- Drift check understands `uv run`, `uvx`, `uv tool run`, `pipx run`, `poetry run`,
  `pdm run`, `hatch run`, `rye run`, `python -m` and `VAR=value` prefixes.
- Home directory written as `~` in generated files; warning for other
  machine-specific paths.
- Lazy commands: `materialize()` placeholders resolved by default; `resolve=` /
  `--resolve` for custom patterns.
- Changes from testing as a new user, before the first release:
  - Typer integration works without the `click` package (Typer ≥ 0.26).
  - **Output**: counting flags (`-vv`), choices of arguments and tuple values, numeric
    ranges, case-insensitive choices, prompts, optional values, argparse aliases,
    `nargs`, mutually exclusive groups and epilogs are shown; the default command is
    marked; "deprecated" appears once; commands are sorted and type names normalised
    so the output is the same on every Click/Typer version; options repeated in three
    or more commands are listed once; `references/commands.md` no longer repeats the
    index.
  - Program name taken from `--program`, the stored setting, the console script or
    the CLI's own name before the skill name; `markdown` warns when it is unknown.
  - Settings (program, `--max-chars`, `--hide-default`) stored in the begin marker
    and reused by `check`, refreshes and `assert_skill_in_sync` (which also accepts
    `max_chars`, `resolve` and `hide_defaults`).
  - `--hide-default NAME` for defaults computed at run time; the stale-block message
    says when only defaults differ.
  - Drift check: continued lines, short option clusters, values given to flags, invalid
    choices, options moved to a subcommand, hidden commands, "did you mean".
  - Command line: one-line errors (exit 2) instead of tracebacks, `--app-dir`,
    `module:func()` targets, functions not called unless named like a parser, `skill`
    refresh without `--name`, `check` prints a success line and the fix command.
