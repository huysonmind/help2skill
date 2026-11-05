"""Typer integration.

Two ways to get ``--llms``:

* ``LlmsOption`` as a parameter of the app callback: root level only, no change
  to your entry point.
* ``command(app)`` as your entry point: ``--llms`` on every command, so
  ``tool sub --llms`` prints just that subtree.
"""

from __future__ import annotations

from typing import Annotated, Any

import typer as _typer

from .click import LLMS_HELP, add_llms_option, print_llms


def _llms_callback(ctx: _typer.Context, value: bool) -> None:
    print_llms(ctx, None, value)


LlmsOption = Annotated[
    bool,
    _typer.Option("--llms", callback=_llms_callback, is_eager=True, help=LLMS_HELP),
]


def command(app: _typer.Typer, name: str | None = None) -> Any:
    """Build the Click command for ``app`` with ``--llms`` at every level.

    Use the result as the console-script entry point::

        main = help2skill.typer.command(app)
    """
    import typer.main

    cmd = typer.main.get_command(app)
    if name:
        cmd.name = name
    return add_llms_option(cmd)
