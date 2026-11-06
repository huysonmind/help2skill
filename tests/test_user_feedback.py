"""Fixes found by testing help2skill as a new user (Click, Typer, argparse, agents)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import textwrap

import click
import pytest
import typer
from click.testing import CliRunner

import help2skill
from help2skill.cli import main
from help2skill.click import add_llms_option, llms_option
from help2skill.sync import check_references
from help2skill.testing import assert_skill_in_sync

# --- a Click CLI with the tricky cases ---------------------------------------------


@click.group(name="ship")
@click.option("-v", "--verbose", count=True, help="More output.")
@click.option("--region", default="eu", help="Region.")
@llms_option()
def ship(verbose: int, region: str) -> None:
    """Ship things."""


@ship.command()
@click.argument("target", type=click.Choice(["api", "web"]))
@click.option("--env", type=click.Choice(["dev", "prod"], case_sensitive=False), default="dev")
@click.option("--replicas", type=click.IntRange(1, 50), default=2)
@click.option("--label", type=(str, click.Choice(["a", "b"])), multiple=True)
@click.option("-f", "--force", is_flag=True)
@click.option("-q", "--quiet", is_flag=True)
@click.option("--token", prompt=True, hide_input=True)
def deploy(target, env, replicas, label, force, quiet, token) -> None:
    """Deploy a target."""


@ship.group()
@click.option("--dry-run", is_flag=True)
def db(dry_run: bool) -> None:
    """Database."""


@db.command()
@click.option("--to", required=True)
def migrate(to: str) -> None:
    """Migrate."""


@ship.command(deprecated=True)
def old() -> None:
    """Old command."""


@ship.command(hidden=True)
def debug() -> None:
    """Hidden."""


@pytest.fixture
def tree():
    return help2skill.introspect(ship)


def test_count_flag_is_not_a_value(tree):
    text = help2skill.render_markdown(tree)
    assert "- `-v, --verbose` (repeat to increase, e.g. -vv)" in text
    assert "INTEGER" not in text
    assert check_references("`ship -vv deploy api`", tree) == []


def test_choices_ranges_and_tuples_are_shown(tree):
    text = help2skill.render_markdown(tree)
    assert "- `TARGET` (one of: api, web; required)" in text
    assert "`--env [dev|prod]` (case-insensitive; default: dev)" in text
    assert "`--replicas INT` (range: 1<=x<=50; default: 2)" in text
    assert "`--label TEXT [a|b]` (repeatable)" in text
    assert "prompts when omitted" in text


def test_deprecated_marked_once(tree):
    text = help2skill.render_markdown(tree)
    assert text.lower().count("deprecated") == 2  # index line + heading
    assert "(DEPRECATED)" not in text


def test_subcommands_sorted_for_stable_output(tree):
    assert [c.name for c in tree.subcommands] == ["db", "deploy", "old"]


def test_check_catches_what_click_rejects(tree):
    text = textwrap.dedent(
        """\
        ```console
        $ ship deploy api \\
            --env prod --bogus 1
        $ ship deploy api -fx
        $ ship deploy api --force=yes
        $ ship deploy api --env qa
        $ ship deploy cli
        $ ship deploy api -fq --env PROD
        $ ship debug
        $ ship db --to x migrate
        $ ship deplyo api
        ```
        """
    )
    problems = check_references(text, tree)
    messages = [(p.line, p.kind, p.message) for p in problems]
    assert messages[0][:2] == (2, "unknown-option")  # continuation line joined
    kinds = [p.kind for p in problems]
    assert kinds == [
        "unknown-option",  # --bogus
        "unknown-option",  # -x in -fx
        "flag-value",
        "invalid-choice",  # --env qa
        "invalid-choice",  # TARGET cli
        "wrong-level-option",  # --to belongs to db migrate
        "unknown-command",  # deplyo
    ]
    assert "place it after `migrate`" in problems[5].message
    assert "did you mean `deploy`?" in problems[6].message


def test_llms_index_points_at_help_without_subcommand_flag(monkeypatch):
    monkeypatch.setenv("HELP2SKILL_LLMS_MAX_CHARS", "200")
    out = CliRunner().invoke(ship, ["--llms"]).output
    assert "run `ship <command> --help`" in out
    add_llms_option(ship)
    out = CliRunner().invoke(ship, ["--llms"]).output
    assert "run `ship <command> --llms`" in out


# --- settings stored in the file -----------------------------------------------------


def test_settings_are_stored_and_reused(tmp_path):
    path = tmp_path / "SKILL.md"
    help2skill.write_skill(
        ship, path, name="ship-skill", program="ship", max_chars=500, hide_defaults=["--region"]
    )
    text = path.read_text()
    assert "<!-- help2skill:begin program=ship max-chars=500 hide-default=--region" in text
    assert (tmp_path / "references" / "commands.md").exists()
    assert "default: eu" not in (tmp_path / "references" / "commands.md").read_text()
    # No settings repeated: the pytest helper and a refresh read them from the file.
    assert_skill_in_sync(ship, path)
    help2skill.write_skill(ship, path)
    assert path.read_text() == text
    path.write_text(text + "\nRun `ship deploy api`.\n")
    assert_skill_in_sync(ship, path)


def test_program_defaults_to_cli_name_not_skill_name(tmp_path):
    path = tmp_path / "SKILL.md"
    help2skill.write_skill(ship, path, name="ship-skill")
    path.write_text(path.read_text() + "\nRun `ship deploy api --bogus`.\n")
    problems = help2skill.check_skill_file(ship, path)
    assert [p.kind for p in problems] == ["unknown-option"]


def test_hide_defaults_and_hint():
    parser = argparse.ArgumentParser(prog="tool")
    parser.add_argument("--workers", type=int, default=7, help="Workers (default: %(default)s).")
    tree = help2skill.introspect(parser, hide_defaults=["workers"])
    assert "7" not in help2skill.render_markdown(tree)
    assert "default: computed at run time" in help2skill.render_markdown(tree)
    with pytest.raises(ValueError, match="no parameter named nope"):
        help2skill.introspect(parser, hide_defaults=["nope"])
    skill = "---\nname: tool\ndescription: x\n---\n" + help2skill.sync.wrap_block(
        help2skill.render_markdown(help2skill.introspect(parser), level=2).replace("7", "9")
    )
    problems = help2skill.check(skill, help2skill.introspect(parser))
    assert "only default values differ" in problems[0].message


def test_pytest_helper_explains_fix(tmp_path):
    path = tmp_path / "SKILL.md"
    help2skill.write_skill(ship, path, name="ship")
    path.write_text(path.read_text().replace("Ship things.", "Old text."))
    with pytest.raises(AssertionError, match="Regenerate the block with: help2skill skill"):
        assert_skill_in_sync(ship, path)


# --- argparse -------------------------------------------------------------------


def build_tool() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool", epilog="Docs: example.org")
    parser.add_argument("--version", action="version", version="1")
    out = parser.add_mutually_exclusive_group()
    out.add_argument("--json", action="store_true")
    out.add_argument("--yaml", action="store_true")
    sub = parser.add_subparsers(dest="cmd")
    build = sub.add_parser("build", aliases=["b", "mk"], help="Build it.")
    build.add_argument("--pair", nargs=2, metavar=("A", "B"))
    build.add_argument("--tags", nargs="*")
    build.add_argument("--opt", nargs="?", const="x")
    build.add_argument("--jobs", type=int, choices=range(1, 65), default=4)
    return parser


def test_argparse_details():
    tree = help2skill.introspect(build_tool())
    text = help2skill.render_markdown(tree)
    assert "- `tool build` (aliases: b, mk): Build it." in text
    assert "Aliases: `b`, `mk`" in text
    assert "`--pair A B`" in text
    assert "`--tags [TAGS ...]`" in text or "`--tags [TEXT ...]`" in text
    assert "`--opt [TEXT]` (value optional)" in text
    assert "`--jobs INT` (range: 1<=x<=64; default: 4)" in text
    assert "Mutually exclusive: `--json`, `--yaml`" in text
    assert "Docs: example.org" in text
    assert "`--version`" in text
    assert check_references("`tool mk --pair 1 2 --tags a b`", tree) == []


# --- command line ------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv, message",
    [
        (["markdown", "no_such_module:cli"], "cannot import 'no_such_module'"),
        (["markdown", "sample_clis:notse"], "did you mean 'notes'?"),
        (["markdown", "sample_clis.py:notes"], "must look like module.path:attribute"),
        (["markdown", "test_user_feedback:test_hide_defaults_and_hint"], "is a function"),
        (["check", "sample_clis:notes", "missing/SKILL.md"], "not found"),
        (["skill", "sample_clis:notes", "--name", "Bad Name"], "invalid skill name"),
    ],
)
def test_errors_are_one_line(argv, message, capsys):
    assert main(argv) == 2
    err = capsys.readouterr().err
    assert message in err
    assert "Traceback" not in err


def test_factory_with_parentheses(capsys):
    assert main(["markdown", "test_user_feedback:build_tool()"]) == 0
    assert "`tool build`" in capsys.readouterr().out


def test_unnamed_parser_warns(tmp_path, monkeypatch, capsys):
    (tmp_path / "unnamed_cli.py").write_text("import argparse\nparser = argparse.ArgumentParser()\n")
    monkeypatch.chdir(tmp_path)
    assert main(["markdown", "unnamed_cli:parser"]) == 0
    assert "program name unknown" in capsys.readouterr().err
    assert main(["markdown", "unnamed_cli:parser", "--program", "tool"]) == 0
    assert capsys.readouterr().out.startswith("# `tool")


def test_app_dir_for_src_layout(tmp_path, monkeypatch, capsys):
    pkg = tmp_path / "src" / "srcpkg_h2s"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "cli.py").write_text("import argparse\nparser = argparse.ArgumentParser(prog='sp')\n")
    monkeypatch.chdir(tmp_path)
    assert main(["markdown", "srcpkg_h2s.cli:parser"]) == 2
    assert "--app-dir src" in capsys.readouterr().err
    assert main(["markdown", "srcpkg_h2s.cli:parser", "--app-dir", "src"]) == 0


def test_check_reports_success(tmp_path, capsys):
    path = tmp_path / "SKILL.md"
    assert main(["skill", "sample_clis:notes", "--name", "notes", "-o", str(path)]) == 0
    assert main(["check", "sample_clis:notes", str(path)]) == 0
    assert "in sync" in capsys.readouterr().out
    # A refresh needs no --name once the file exists.
    assert main(["skill", "sample_clis:notes", "-o", str(path)]) == 0


# --- size -----------------------------------------------------------------------------


def test_shared_options_listed_once():
    @click.group(name="big")
    def big() -> None:
        pass

    for name in ("a", "b", "c", "d"):

        @big.command(name=name)
        @click.option(
            "--fmt",
            type=click.Choice(["json", "csv", "table", "markdown"]),
            help="Output format for the rows printed by this command.",
        )
        @click.option("--own", help="Own option.")
        def _cmd(fmt, own) -> None:
            pass

    text = help2skill.render_markdown(help2skill.introspect(big))
    assert text.count("`--fmt [json|csv|table|markdown]`") == 1
    assert text.count("- Shared options: `--fmt`") == 4
    assert text.count("--own TEXT") == 4


def test_reference_file_does_not_repeat_the_index(tmp_path):
    path = tmp_path / "SKILL.md"
    help2skill.write_skill(ship, path, name="ship", max_chars=200)
    reference = (tmp_path / "references" / "commands.md").read_text()
    assert "Commands (all levels)" not in reference
    assert "Commands (all levels)" in path.read_text()


# --- Typer without the click package ------------------------------------------------


def test_typer_integration_without_click_installed(tmp_path):
    if not hasattr(typer, "_click"):
        pytest.skip("this Typer still depends on Click")
    script = tmp_path / "typer_only.py"
    script.write_text(
        textwrap.dedent(
            """\
            import sys
            sys.modules["click"] = None  # as if click were not installed
            import typer
            import help2skill.typer
            from help2skill.typer import LlmsOption

            app = typer.Typer()

            @app.callback()
            def main(llms: LlmsOption = False):
                "Tool."

            @app.command()
            def hello(name: str):
                "Say hi."

            cmd = help2skill.typer.command(app, name="tool")
            cmd(["hello", "--llms"])
            """
        )
    )
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert " hello NAME`\n\nSay hi." in result.stdout
