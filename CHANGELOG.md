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
