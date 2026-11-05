# help2skill: short spec (v0.1)

## Problem
Coding agents call CLIs constantly but learn them from stale training data or by
guessing. In 2026 large Python CLIs started shipping agent docs by hand:
Hugging Face (`hf skills`, generated from the Click tree), Modal (`modal skills`),
SkyPilot (`agent/scripts/generate_references.py`), AWS CLI (`aws configure agent-toolkit`),
dbt-charts, Keboola. Each wrote its own generator; smaller projects copy-paste
`gen_skill.py` scripts. Typer ≥ 0.26 vendors Click, which silently breaks those
scripts' `isinstance(cmd, click.Group)` checks.

## Scope of v0.1
1. **Introspection** of Click, Typer (old and vendored-Click) and argparse into one
   neutral model (`Command`, `Param`). Duck-typed; zero runtime dependencies.
2. **Markdown reference** (`render_markdown`): full path in every heading, an index
   of all commands at the root, per-param type / required / repeatable / default /
   env var / help. Deterministic output.
3. **`--llms` flag**: Click decorator, `add_llms_option` for any built tree,
   Typer `LlmsOption` (root) and `help2skill.typer.command(app)` (every level).
4. **SKILL.md**: frontmatter validated against Agent Skills rules (name ≤ 64,
   `[a-z0-9-]`, description ≤ 1024, no angle brackets); generated block between
   markers, hand-written text preserved on refresh.
5. **Drift check**: stale block; hand-written examples that use a missing subcommand,
   a missing option, or an option at the wrong level. Handles default-command groups.
   CLI `help2skill check` (exit 1) and `help2skill.testing.assert_skill_in_sync`.

## Non-goals (v0.1)
- Installing skills into agent folders (use library-skills).
- Detecting the calling agent / auto JSON output (planned, via existing detectors).
- Static analysis without importing the CLI (claude-skill-forge does that).

## Output contract
Markdown output is a public interface: changes to it are noted in the changelog,
because users commit generated blocks and the drift check compares them verbatim.
