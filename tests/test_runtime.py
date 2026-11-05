from __future__ import annotations

import click
import typer.testing
from click.testing import CliRunner
from sample_clis import notes, typer_app

import help2skill.typer
from help2skill.click import add_llms_option


def test_click_llms_flag_prints_reference():
    result = CliRunner().invoke(notes, ["--llms"], prog_name="notes")
    assert result.exit_code == 0, result.output
    assert result.output.startswith("# `notes [OPTIONS] COMMAND [ARGS]...`")
    assert "## `notes db migrate [OPTIONS]`" in result.output


def test_click_add_llms_option_scopes_to_subcommand():
    @click.group()
    def tool() -> None:
        pass

    @tool.command()
    @click.option("--n", type=int)
    def run(n: int) -> None:
        """Run it."""

    add_llms_option(tool)
    add_llms_option(tool)  # idempotent
    assert sum(p.name == "llms" for p in tool.commands["run"].params) == 1
    result = CliRunner().invoke(tool, ["run", "--llms"], prog_name="tool")
    assert result.exit_code == 0, result.output
    assert result.output.startswith("# `tool run [OPTIONS]`\n\nRun it.")
    assert "--n INT" in result.output


def test_typer_root_llms_option():
    result = typer.testing.CliRunner().invoke(typer_app, ["--llms"], prog_name="notes")
    assert result.exit_code == 0, result.output
    assert "## `notes add [OPTIONS] TITLE`" in result.output
    assert "--llms" not in result.output


def test_typer_normal_invocation_still_works():
    result = typer.testing.CliRunner().invoke(typer_app, ["add", "hello"], prog_name="notes")
    assert result.exit_code == 0, result.output


def test_typer_command_adds_flag_everywhere():
    cmd = help2skill.typer.command(typer_app, name="notes")
    result = CliRunner().invoke(cmd, ["db", "migrate", "--llms"], prog_name="notes")
    assert result.exit_code == 0, result.output
    assert result.output.startswith("# `notes db migrate [OPTIONS]` (deprecated)\n\nRun schema migrations.")
