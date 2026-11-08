"""help2skill lint: check the command lines in a README and docs/ against the CLI."""

from __future__ import annotations

import textwrap

import pytest
from sample_clis import notes

import help2skill
from help2skill.cli import main
from help2skill.lint import find_docs, lint_text
from help2skill.testing import assert_docs_in_sync

TARGET = "sample_clis:notes"


@pytest.fixture
def tree():
    return help2skill.introspect(notes, "notes")


def kinds(text, tree, filename="README.md"):
    return [(p.line, p.kind) for p in lint_text(textwrap.dedent(text), tree, filename=filename).problems]


def test_markdown_fences_and_spans(tree):
    text = """\
    Run `notes add milk --colour red` to add one.

    ```bash
    notes add milk --priority urgent
    notes ad milk
    ```
    """
    assert kinds(text, tree) == [(1, "unknown-option"), (4, "invalid-choice"), (5, "unknown-command")]


def test_other_languages_are_skipped(tree):
    text = """\
    ```python
    notes = notes.add(title)
    ```

    ```toml
    notes = "add --bad"
    ```
    """
    assert kinds(text, tree) == []


def test_console_blocks_with_prompts_skip_output(tree):
    text = """\
    ```console
    $ notes add milk --tag home
    notes add: done --weird
    $ notes add milk --nope
    ```
    """
    assert kinds(text, tree) == [(4, "unknown-option")]


def test_console_block_without_prompts_is_all_commands(tree):
    assert kinds("```console\nnotes add milk --nope\n```\n", tree) == [(2, "unknown-option")]


def test_missing_argument_only_in_blocks(tree):
    assert kinds("Use `notes add` to add.\n\n```sh\nnotes add\n```\n", tree) == [(4, "missing-argument")]


def test_ignore_marker(tree):
    text = """\
    <!-- help2skill: ignore -->
    ```bash
    notes plugin-command --x
    ```

    `notes add milk --nope` (help2skill: ignore)
    """
    assert kinds(text, tree) == []


def test_line_continuation(tree):
    text = "```bash\nnotes add milk \\\n  --priority urgent\n```\n"
    assert kinds(text, tree) == [(2, "invalid-choice")]


RST = """\
Usage
=====

Add a note with ``notes add milk --colour red``.

.. code-block:: bash
   :caption: Example

   notes add milk --priority urgent

.. code-block:: python

   notes = notes.add("--bad")

Literal blocks only count their prompt lines::

    $ notes ad milk
    notes ad: output line

.. prompt:: bash $

   notes add milk --nope

.. help2skill: ignore

.. code-block:: bash

   notes broken --x
"""


def test_restructuredtext(tree):
    assert kinds(RST, tree, filename="usage.rst") == [
        (4, "unknown-option"),
        (9, "invalid-choice"),
        (17, "unknown-command"),
        (22, "unknown-option"),
    ]


def test_generated_block_is_skipped(tree, tmp_path):
    path = help2skill.write_skill(notes, tmp_path / "SKILL.md", name="notes")
    result = lint_text(path.read_text(), tree, filename="SKILL.md")
    assert result.problems == []


def test_find_docs_skips_changelogs_and_build_dirs(tmp_path):
    for name in (
        "README.md",
        "docs/guide.md",
        "docs/api/usage.rst",
        "docs/page.mdx",
        "docs/changelog.md",
        "docs/HISTORY.rst",
        "docs/release-notes/v1.md",
        "docs/_build/out.md",
        "docs/legacy/old.md",
        "docs/data.json",
        ".venv/lib/x.md",
    ):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("x")
    found = find_docs([tmp_path / "README.md", tmp_path / "docs"], exclude=["*/legacy/*"])
    assert [p.relative_to(tmp_path).as_posix() for p in found] == [
        "README.md",
        "docs/api/usage.rst",
        "docs/guide.md",
        "docs/page.mdx",
    ]
    # A changelog named explicitly is checked.
    assert find_docs([tmp_path / "docs/changelog.md"]) == [tmp_path / "docs/changelog.md"]


def test_check_docs_and_pytest_helper(tmp_path):
    good = tmp_path / "good.md"
    good.write_text("```bash\nnotes add milk --tag home\n```\n")
    bad = tmp_path / "bad.md"
    bad.write_text("```bash\nnotes add milk --colour red\n```\n")
    results = help2skill.check_docs(notes, [good, bad], program="notes")
    assert [(r.path.name, r.checked, len(r.problems)) for r in results] == [
        ("bad.md", 1, 1),
        ("good.md", 1, 0),
    ]
    assert_docs_in_sync(notes, [good], program="notes")
    with pytest.raises(AssertionError, match=r"bad.md:2: `notes add` has no option `--colour`"):
        assert_docs_in_sync(notes, [bad], program="notes")


def test_cli_lint(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "use.md").write_text("```bash\nnotes add milk --colour red\n```\n")
    (tmp_path / "README.md").write_text("Run `notes add milk`.\n")
    monkeypatch.chdir(tmp_path)
    assert main(["lint", TARGET, "--program", "notes"]) == 1
    out, _ = capsys.readouterr()
    assert "docs/use.md:2: `notes add` has no option `--colour`" in out.replace("\\", "/")
    assert "1 problem; 2 `notes` command lines checked in 2 of 2 files" in out

    assert main(["lint", TARGET, "--program", "notes", "README.md", "--format", "github"]) == 0
    out, _ = capsys.readouterr()
    assert "no problems; 1 `notes` command line checked in 1 of 1 file" in out

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert main(["lint", TARGET, "--program", "notes", "docs"]) == 1
    out, _ = capsys.readouterr()
    assert "::error file=docs/use.md,line=2,title=help2skill unknown-option::" in out


def test_cli_lint_without_docs(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["lint", TARGET, "--program", "notes"]) == 2
    assert "no README or docs/" in capsys.readouterr().err


def test_command_substitution_is_one_value(tree):
    assert kinds("```bash\nnotes add $(date --iso --utc) --tag home\n```\n", tree) == []


def test_optional_arguments_before_required_ones():
    import argparse

    parser = argparse.ArgumentParser(prog="http")
    parser.add_argument("--version", action="version", version="1.0")
    parser.add_argument("method", nargs="?")
    parser.add_argument("url")
    parser.add_argument("items", nargs="*")
    tree = help2skill.introspect(parser)
    assert kinds("```bash\nhttp example.org\nhttp --version\nhttp\n```\n", tree) == [(4, "missing-argument")]


def test_remainder_and_double_dash():
    import argparse

    parser = argparse.ArgumentParser(prog="tool")
    sub = parser.add_subparsers()
    run = sub.add_parser("run")
    run.add_argument("script")
    run.add_argument("args", nargs=argparse.REMAINDER)
    sub.add_parser("rm").add_argument("names", nargs="+")
    tree = help2skill.introspect(parser)
    text = "```bash\ntool run test --user --provided\ntool rm -- -odd-name\ntool rm\n```\n"
    assert kinds(text, tree) == [(4, "missing-argument")]


def test_click_passthrough_and_plugin_names():
    import click

    @click.group()
    def tool() -> None:
        pass

    tool.default_cmd_name = "query"  # type: ignore[attr-defined]  # as click-default-group sets it

    @tool.command(context_settings={"ignore_unknown_options": True})
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    def run(args: tuple[str, ...]) -> None:
        pass

    @tool.command()
    @click.argument("sql")
    def query(sql: str) -> None:
        pass

    tree = help2skill.introspect(tool, "tool")
    text = "```bash\ntool run python -m pip --pre\ntool hello-world\ntool 'select 1' --nope\n```\n"
    assert kinds(text, tree) == [(4, "unknown-option")]


def test_prose_with_slashes(tree):
    assert kinds("Never run `notes add/notes db` here.\n", tree) == []


def test_root_version_option_is_accepted(tree):
    assert kinds("```bash\nnotes --version\n```\n", tree) == []


def test_diagram_blocks_are_skipped(tree):
    text = """\
    ```
    browser ──► notes add milk --nope
                notes   (or --mock)
    ```

    ```bash
    # ─ a comment, but a shell block is still checked
    notes add milk --nope
    ```
    """
    assert kinds(text, tree) == [(8, "unknown-option")]


def test_elided_arguments_stop_the_check(tree):
    text = "```bash\nnotes add ... --tag home\nnotes add \u2026 milk extra\nnotes add ... --nope\n```\n"
    assert kinds(text, tree) == []


def test_hidden_options_are_accepted():
    import argparse

    import click

    @click.group()
    def tool() -> None:
        pass

    @tool.command()
    @click.option("--json", "as_json", is_flag=True, hidden=True)
    @click.option("--limit", type=int, hidden=True)
    def ls(as_json: bool, limit: int) -> None:
        pass

    tree = help2skill.introspect(tool, "tool")
    assert "--json" not in help2skill.render_markdown(tree)
    assert kinds("```bash\ntool ls --json --limit 5\ntool ls --nope\n```\n", tree) == [(3, "unknown-option")]

    parser = argparse.ArgumentParser(prog="app")
    parser.add_argument("--debug-dump", help=argparse.SUPPRESS)
    tree = help2skill.introspect(parser)
    assert kinds("```bash\napp --debug-dump out.txt\n```\n", tree) == []


def test_wildcards_name_several_commands(tree):
    text = (
        "```bash\nnotes ad* milk\nnotes {add,rm} milk\nnotes add milk --tag-*\nnotes add milk --nope\n```\n"
    )
    assert kinds(text, tree) == [(5, "unknown-option")]


def test_mermaid_labels_and_table_rows(tree):
    text = """\
    ```mermaid
    flowchart TD
      A[Start] --> B[notes add milk --nope]
      B -->|notes ad milk| C{done?}
      %% D[notes old-command]
    ```

    | Command | Options |
    |---|---|
    | `notes add milk` | `--tag home`, `--colour` |
    | `notes add milk` | Adds a note; see `notes ad`. |
    | `notes add / rm` | `--colour` |
    """
    assert kinds(text, tree) == [
        (3, "unknown-option"),
        (4, "unknown-command"),
        (10, "unknown-option"),
        (11, "unknown-command"),
    ]


def test_global_options_anywhere(tmp_path, monkeypatch, capsys):
    import click

    @click.group()
    @click.option("--pretty", is_flag=True)
    def tool(pretty: bool) -> None:
        pass

    @tool.command()
    def schema() -> None:
        pass

    doc = tmp_path / "use.md"
    doc.write_text("```bash\ntool schema --pretty\n```\n")
    assert [p.kind for r in help2skill.check_docs(tool, [doc], program="tool") for p in r.problems] == [
        "wrong-level-option"
    ]
    assert help2skill.check_docs(tool, [doc], program="tool", global_options=True)[0].problems == []
    assert_docs_in_sync(tool, [doc], program="tool", global_options=True)
