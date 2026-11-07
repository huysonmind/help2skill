---
name: help2skill
description: "Use help2skill to give a Python CLI (Click, Typer, argparse, cyclopts or plumbum) an --llms flag, generate or refresh its SKILL.md, and check hand-written CLI examples against the real command tree. Use when adding agent docs to a CLI or when a help2skill check fails."
---

<!-- help2skill:begin program=help2skill max-chars=30000 (generated from the CLI; edit outside this block) -->
## `help2skill [OPTIONS] COMMAND [ARGS]...`

Generate LLM-ready docs and SKILL.md files from Click, Typer, argparse, cyclopts and plumbum CLIs.

TARGET is the import path of the CLI object, e.g. mypkg.cli:app. For a function that builds an argparse parser, write mypkg.cli:build_parser() (with parentheses).

Options:
- `--version`: show program's version number and exit

Commands (all levels):
- `help2skill markdown`: Print the Markdown reference for a CLI.
- `help2skill skill`: Create a SKILL.md, or refresh its generated block.
- `help2skill check`: Exit 1 if a SKILL.md has drifted from the CLI.

Shared options (listed by name in the commands that accept them):
- `--program TEXT`: Program name users type (default: stored in the file, else the console script that points at TARGET, else the CLI's own name)
- `--hide-default NAME` (repeatable): Leave out the default of this parameter (name or option), e.g. one computed at run time; repeatable. Stored in the file.
- `--app-dir DIR`: Import TARGET from this directory, e.g. src (default: the current directory)
- `--resolve MODULE:FUNC`: Function that turns a lazy placeholder command into the real command
- `--from-main`: TARGET is a main() function that builds an argparse parser and parses sys.argv: run it until it parses, and use that parser. Code in main() before parsing runs.

### `help2skill markdown [OPTIONS] TARGET`

Print the Markdown reference for a CLI.

Arguments:
- `TARGET` (text; required): CLI object, e.g. mypkg.cli:app

Options:
- `--max-chars INT`: Print only an index when the reference is longer than this (default: 0 = no limit)
- Shared options: `--program`, `--hide-default`, `--app-dir`, `--resolve`, `--from-main`

### `help2skill skill [OPTIONS] TARGET`

Create a SKILL.md, or refresh its generated block.

Arguments:
- `TARGET` (text; required): CLI object, e.g. mypkg.cli:app

Options:
- `--name TEXT`: Skill name: lowercase letters, digits, hyphens (needed to create the file)
- `--description TEXT`: Skill description (default: from the CLI help)
- `-o, --output PATH`: SKILL.md path (default: skills/<name>/SKILL.md)
- `--max-chars INT`: Above this size, keep an index in SKILL.md and the full reference in references/commands.md (default: 30000, or the value stored in the file; 0 = never split)
- Shared options: `--program`, `--hide-default`, `--app-dir`, `--resolve`, `--from-main`

### `help2skill check [OPTIONS] TARGET PATH`

Exit 1 if a SKILL.md has drifted from the CLI.

Arguments:
- `TARGET` (text; required): CLI object, e.g. mypkg.cli:app
- `PATH` (path; required): SKILL.md to check

Options:
- `--max-chars INT`: Override the value stored in the file
- Shared options: `--program`, `--hide-default`, `--app-dir`, `--resolve`, `--from-main`
<!-- help2skill:end -->

## How to use it

TARGET is an import path, not a file path: `mypkg.cli:app`, never `src/mypkg/cli.py`.
Run the commands from the project root, inside the project's environment
(`uv run help2skill …` with uv). For a `src/` layout that is not installed, add
`--app-dir src`.

### Add `--llms` to a CLI

- Click: decorate the root group with `@llms_option()` from `help2skill.click`, or
  call `add_llms_option(cli)` to get the flag on every subcommand.
- Typer: add `llms: LlmsOption = False` (from `help2skill.typer`) to the callback, or
  build the command with `help2skill.typer.command(app, name="mytool")` and point the
  console script at it.
- argparse, cyclopts and plumbum have no `--llms` hook; print the reference instead
  (`--from-main` when an argparse parser is only built inside `main()`):

```console
help2skill markdown "mypkg.cli:build_parser()"
```

### Create or refresh a SKILL.md

```console
help2skill skill mypkg.cli:app --name mytool --description "Use mytool to ..." -o src/mypkg/.agents/skills/mytool/SKILL.md
```

Running the same command again (without `--name`) refreshes only the block between
the `help2skill:begin` and `help2skill:end` markers. Write guidance and examples
outside that block; never edit inside it. The begin marker stores `--program`,
`--max-chars` and `--hide-default`, so later runs need only TARGET and the path.

### Fix a failing check

```console
help2skill check mypkg.cli:app src/mypkg/.agents/skills/mytool/SKILL.md
```

- "stale": the CLI changed. Rerun `help2skill skill` with the same TARGET and path.
  If only defaults differ between machines (CPU count, dates), add
  `--hide-default NAME` once; it is remembered.
- "unknown option", "unknown command", "misplaced option", "invalid choice": a
  hand-written example is wrong. Fix the example to match the reference block, using
  the "did you mean" suggestion; do not change the CLI to fit the docs.
- An import error: check TARGET, `--app-dir`, and that the project's environment is
  active.

In tests, `help2skill.testing.assert_skill_in_sync(app, path)` runs the same check.
