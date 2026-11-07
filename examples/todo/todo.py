"""A small Typer CLI used to show what help2skill generates.

Try it from the repository root:

    uv run --with typer python examples/todo/todo.py --llms
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

import typer

from help2skill.typer import command

app = typer.Typer(help="Keep a to-do list in a local file.")
tags = typer.Typer(help="Manage tags.")
app.add_typer(tags, name="tag")


class Priority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


@app.command()
def add(
    text: str,
    priority: Priority = Priority.normal,
    tag: Annotated[list[str] | None, typer.Option("--tag", "-t", help="Tag to attach.")] = None,
    due: Annotated[str | None, typer.Option(help="Due date, YYYY-MM-DD.", envvar="TODO_DUE")] = None,
) -> None:
    """Add a task."""


@app.command("list")
def list_(
    done: Annotated[bool, typer.Option("--done/--open", help="Show finished or open tasks.")] = False,
    limit: Annotated[int, typer.Option(min=1, max=500, help="Maximum tasks to show.")] = 20,
) -> None:
    """List tasks."""


@app.command()
def finish(task_id: int) -> None:
    """Mark a task as done."""


@tags.command("rename")
def tag_rename(old: str, new: str) -> None:
    """Rename a tag on every task."""


main = command(app, name="todo")

if __name__ == "__main__":
    main(prog_name="todo")
