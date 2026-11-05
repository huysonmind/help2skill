"""The same small CLI written with Click, Typer and argparse."""

from __future__ import annotations

import argparse
import enum
from typing import Annotated

import click
import typer

from help2skill.click import llms_option
from help2skill.typer import LlmsOption

# --- Click -------------------------------------------------------------------


@click.group(help="Manage notes.")
@click.option("--verbose", "-v", is_flag=True, help="Show more output.")
@llms_option()
def notes(verbose: bool) -> None:
    pass


@notes.command(name="add")
@click.argument("title")
@click.option("--tag", "tags", multiple=True, help="Tag to attach.")
@click.option("--priority", type=click.Choice(["low", "high"]), default="low", show_default=True)
@click.option("--token", envvar="NOTES_TOKEN", help="API token.")
def add(title: str, tags: tuple[str, ...], priority: str, token: str | None) -> None:
    """Add a note.

    The note is stored locally.
    """


@notes.group(name="db")
def db() -> None:
    """Database maintenance."""


@db.command(name="migrate", deprecated=True)
@click.option("--dry-run", is_flag=True)
def migrate(dry_run: bool) -> None:
    """Run schema migrations."""


@notes.command(name="secret", hidden=True)
def secret() -> None:
    """Hidden command."""


# --- Typer -------------------------------------------------------------------


class Priority(str, enum.Enum):
    low = "low"
    high = "high"


typer_app = typer.Typer(help="Manage notes.", add_completion=True)
typer_db = typer.Typer(help="Database maintenance.")
typer_app.add_typer(typer_db, name="db")


@typer_app.callback()
def typer_main(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show more output.")] = False,
    llms: LlmsOption = False,
) -> None:
    pass


@typer_app.command("add")
def typer_add(
    title: Annotated[str, typer.Argument()],
    tag: Annotated[list[str], typer.Option("--tag", help="Tag to attach.")] = [],  # noqa: B006
    priority: Priority = Priority.low,
    token: Annotated[str, typer.Option(envvar="NOTES_TOKEN", help="API token.")] = "",
) -> None:
    """Add a note.

    The note is stored locally.
    """


@typer_db.command("migrate", deprecated=True)
def typer_migrate(dry_run: bool = False) -> None:
    """Run schema migrations."""


# --- argparse ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes", description="Manage notes.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show more output.")
    sub = parser.add_subparsers(dest="command")
    add_p = sub.add_parser(
        "add", help="Add a note.", description="Add a note.\n\nThe note is stored locally."
    )
    add_p.add_argument("title")
    add_p.add_argument("--tag", action="append", help="Tag to attach.")
    add_p.add_argument("--priority", choices=["low", "high"], default="low")
    add_p.add_argument("--token", help=argparse.SUPPRESS)
    db_p = sub.add_parser("db", help="Database maintenance.", aliases=["database"])
    db_sub = db_p.add_subparsers(dest="db_command")
    mig = db_sub.add_parser("migrate", help="Run schema migrations.")
    mig.add_argument("--dry-run", action="store_true")
    mig.add_argument("--steps", type=int, default=1, help="How many steps (default: %(default)s).")
    return parser
