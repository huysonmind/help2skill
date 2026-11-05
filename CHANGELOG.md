# Changelog

All notable changes are listed here. The generated Markdown format is part of the
public interface: any change to it is called out under **Output**.

## Unreleased

## 0.1.0 (not yet released)
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
