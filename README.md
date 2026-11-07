# help2skill

> **Status: alpha.** The output format may still change before 1.0.

`--help` for LLM agents. Make a Click, Typer, argparse, cyclopts or plumbum CLI easy for coding agents
(Claude Code, Codex, Cursor, Gemini CLI…) to use correctly:

- **`--llms` flag**: prints a compact Markdown reference of the command tree (every
  subcommand, argument, option, choice, default and env var), generated from the CLI
  itself, so it never goes stale.
- **`SKILL.md` export**: writes an [Agent Skills](https://agentskills.io) file whose
  reference block is regenerated from the CLI while your hand-written guidance is kept.
- **Drift check for CI**: fails when the generated block is stale, or when hand-written
  examples mention a subcommand or option that does not exist (or an option placed at
  the wrong level, e.g. a group option after the subcommand).

No runtime dependencies. Works with Typer ≥ 0.26 (vendored Click), where code that does
`isinstance(cmd, click.Group)` silently finds nothing.

## What it looks like

```console
$ todo --llms
# `todo COMMAND [ARGS]...`

Keep a to-do list in a local file.

Commands (all levels):
- `todo add`: Add a task.
- `todo finish`: Mark a task as done.
- `todo list`: List tasks.
- `todo tag rename`: Rename a tag on every task.

## `todo add [OPTIONS] TEXT`
...
- `--priority [low|normal|high]` (default: normal)
- `-t, --tag TEXT` (repeatable): Tag to attach.
...
```

When a hand-written example drifts from the CLI, CI says so:

```console
$ help2skill check todo:main SKILL.md
SKILL.md: line 11: `todo list` has no option `--status` [unknown-option]
SKILL.md: line 12: `todo` has no subcommand `done` [unknown-command]
```

More in [`examples/`](https://github.com/huysonmind/help2skill/tree/main/examples):
a Typer app, sqlite-utils (48 commands) and pipx (argparse).

## Does it help?

In a [small experiment](https://github.com/huysonmind/help2skill/tree/main/evals/agent_commands)
(16 tasks on llm and sqlite-utils, Claude Sonnet and Haiku), agents given the generated
SKILL.md wrote 32/32 correct commands with no `--help` calls. Exploring with `--help`
got 31/32 with 65 calls; answering from memory got 28/32. One run per cell, so treat it
as a first signal.

## Quick start

### Click

```python
import click
from help2skill.click import llms_option


@click.group()
@llms_option()
def cli(): ...
```

```console
$ mytool --llms
```

`llms_option()` adds the flag to the root only, which prints the whole tree. To get
`--llms` on every subcommand too (`mytool db --llms` prints just that subtree):

```python
from help2skill.click import add_llms_option

add_llms_option(cli)
```

### Typer

Root flag, no change to your entry point:

```python
import typer
from help2skill.typer import LlmsOption

app = typer.Typer()


@app.callback()
def main(llms: LlmsOption = False): ...
```

Or `--llms` at every level: build the command once and make it your console script.

```python
# mytool/cli.py
import help2skill.typer

main = help2skill.typer.command(app, name="mytool")
```

```toml
# pyproject.toml
[project.scripts]
mytool = "mytool.cli:main"
```

No `click` package is needed with Typer ≥ 0.26, which ships its own copy.

### argparse

argparse has no hook for an extra flag, so use the command line (or the Python API):

```console
$ help2skill markdown mytool.cli:parser
$ help2skill markdown "mytool.cli:build_parser()"   # a function that returns the parser
$ help2skill markdown mytool.cli:main --from-main     # main() builds and parses the parser
```

`--from-main` is for scripts whose parser only exists inside `main()`: help2skill runs
`main()` until it calls `parse_args()` and stops there. Whatever `main()` does before
parsing still runs, so read it first.

### cyclopts and plumbum

Point the command line or `help2skill.introspect` at the cyclopts `App` or the plumbum
`cli.Application` subclass (the class, not an instance):

```console
$ help2skill markdown mytool.cli:app        # cyclopts.App
$ help2skill markdown mytool.cli:MyTool     # plumbum cli.Application subclass
```

There is no `--llms` flag for them yet; use `help2skill skill` and `check`.

### Large CLIs

`--llms` prints the full reference when it fits in 20,000 characters (about 5k tokens).
Above that it prints the top-level help plus an index of every command, and tells the
agent how to ask for one command (`mytool <command> --llms`, or `--help` when only the
root has the flag). Set `HELP2SKILL_LLMS_MAX_CHARS=0` for everything. Options repeated
identically in three or more commands are described once, under "Shared options".

### Lazy commands

Click's documented `LazyGroup` pattern works as is. Placeholder commands with a
`materialize()` method are loaded automatically; for anything else pass
`resolve=` (Python API) or `--resolve module:func` (command line).

## SKILL.md and drift checks

```console
$ help2skill skill mytool.cli:app --name mytool --description "Use mytool to ..." \
    -o src/mytool/.agents/skills/mytool/SKILL.md
$ help2skill check mytool.cli:app src/mytool/.agents/skills/mytool/SKILL.md
```

`skill` creates the file, or refreshes only the block between
`<!-- help2skill:begin … -->` and `<!-- help2skill:end -->` if it already exists
(`--name` is then optional). Write your own guidance above or below the block.

help2skill ships its own skill, made with itself:
[`src/help2skill/.agents/skills/help2skill/SKILL.md`](https://github.com/huysonmind/help2skill/blob/main/src/help2skill/.agents/skills/help2skill/SKILL.md).

**Program name.** Commands are written with the name users type. help2skill uses
`--program` if given, else the installed console script that points at the target,
else the CLI's own name (`@click.group(name="mytool")`, `ArgumentParser(prog="mytool")`),
else the skill name. `markdown` warns when it can only guess.

**Settings are stored in the file.** The begin marker records the program name,
`--max-chars` and `--hide-default`, so `check`, a refresh and the pytest helper reuse
them without repeating any option.

**Stable in CI.** The output does not depend on the machine or on the Click/Typer
version: commands are sorted, type names are normalised and your home directory is
written as `~` (other machine-specific paths trigger a warning). A default computed at
run time (CPU count, today's date) would still differ, so leave it out:

```console
$ help2skill skill mytool.cli:app -o SKILL.md --hide-default workers --hide-default --since
```

When the reference is longer than 30,000 characters, `SKILL.md` keeps an index and the
full reference goes to `references/commands.md` beside it (fully generated; agents read
it on demand). Change the limit with `--max-chars` (0 = never split).

**What the check catches** in code spans and fenced blocks of your hand-written text:
unknown subcommands and options (with "did you mean"), options at the wrong level,
values not among an option's or argument's choices, values given to flags,
single-letter clusters such as `-fq`, and (in fenced blocks) missing required
arguments. Lines continued with `\` are joined, and lines are recognised with launchers
in front: `uv run [--with …] mytool …`, `uvx`, `pipx run`, `poetry run`,
`python -m mytool`, `python path/to/mytool.py …`, `./mytool`, `VAR=value mytool …`.
`check` also accepts the target module's file name (`python scripts/build.py …` for
`build:parser`). Placeholders such as `<file>`, `<two words>`, `FILE`, `my_name` and
`a|b|c` are not checked.

Shipping the skill inside your package under `.agents/skills/<name>/` makes it
installable with [library-skills](https://github.com/tiangolo/library-skills). With
setuptools, add the folder to `package-data`; hatchling includes it by default.

In pytest (build the path from `__file__` so the test runs from any directory):

```python
from pathlib import Path

from help2skill.testing import assert_skill_in_sync
from mytool.cli import app

SKILL = Path(__file__).parents[1] / "src/mytool/.agents/skills/mytool/SKILL.md"


def test_skill_in_sync():
    assert_skill_in_sync(app, SKILL)
```

With a `src/` layout that is not installed, pass `--app-dir src` to the command line.

As a [pre-commit](https://pre-commit.com) hook (runs in your project's environment):

```yaml
repos:
  - repo: local
    hooks:
      - id: help2skill-check
        name: SKILL.md in sync with the CLI
        entry: uv run help2skill check mytool.cli:app src/mytool/.agents/skills/mytool/SKILL.md
        language: system
        pass_filenames: false
```

## Python API

```python
import help2skill

tree = help2skill.introspect(app, "mytool")  # Click, Typer, argparse, cyclopts, plumbum
print(help2skill.render_markdown(tree))
help2skill.write_skill(app, "SKILL.md", name="mytool")
problems = help2skill.check_skill_file(app, "SKILL.md")
```

## Security

`help2skill` imports the module you point it at, the same as running your CLI. It calls
a function only when you write `module:func()` or the function's name contains
"parser"; it never calls your `main()`. Generated files copy your help text verbatim, so review them
for machine-specific values before committing. See [SECURITY.md](https://github.com/huysonmind/help2skill/blob/main/SECURITY.md).

## License

[MIT](https://github.com/huysonmind/help2skill/blob/main/LICENSE). Built with AI assistance (Claude).
