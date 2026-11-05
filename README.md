# help2skill

> **Status: alpha.** The output format may still change before 1.0.

`--help` for LLM agents. Make a Click, Typer or argparse CLI easy for coding agents
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

To get `--llms` on every subcommand (`mytool db --llms` prints just that subtree):

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

Or `--llms` at every level, using the returned Click command as the entry point:

```python
import help2skill.typer

main = help2skill.typer.command(app, name="mytool")
```

### argparse

```console
$ help2skill markdown mytool.cli:build_parser --program mytool
```

## SKILL.md and drift checks

```console
$ help2skill skill mytool.cli:app --name mytool --description "Use mytool to ..." \
    -o src/mytool/.agents/skills/mytool/SKILL.md
$ help2skill check mytool.cli:app src/mytool/.agents/skills/mytool/SKILL.md
```

`skill` creates the file, or refreshes only the block between
`<!-- help2skill:begin … -->` and `<!-- help2skill:end -->` if it already exists.
Write your own guidance above or below the block.

Shipping the skill inside your package under `.agents/skills/<name>/` makes it
installable with [library-skills](https://github.com/tiangolo/library-skills).

In pytest:

```python
from help2skill.testing import assert_skill_in_sync
from mytool.cli import app


def test_skill_in_sync():
    assert_skill_in_sync(app, "src/mytool/.agents/skills/mytool/SKILL.md")
```

## Python API

```python
import help2skill

tree = help2skill.introspect(app, "mytool")  # Click, Typer or argparse
print(help2skill.render_markdown(tree))
help2skill.write_skill(app, "SKILL.md", name="mytool")
problems = help2skill.check_skill_file(app, "SKILL.md")
```

## Security

`help2skill` imports the module you point it at (and calls it if it is a function), the
same as running your CLI. Generated files copy your help text verbatim, so review them
for machine-specific values before committing. See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). Built with AI assistance (Claude).
