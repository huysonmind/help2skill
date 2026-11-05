"""Click integration: a ``--llms`` flag that prints the Markdown reference."""

from __future__ import annotations

from typing import Any

import click as _click

from ._click import from_context
from .render import render_markdown

LLMS_HELP = "Print a Markdown reference of this command for LLM agents, then exit."


def print_llms(ctx: Any, param: Any, value: bool) -> None:
    """Eager option callback usable with Click and Typer-built commands."""
    if not value or ctx.resilient_parsing:
        return
    _click.echo(render_markdown(from_context(ctx)), nl=False)
    ctx.exit()


def llms_option(*param_decls: str, **kwargs: Any):
    """Decorator adding ``--llms`` to one Click command or group.

    On a group it prints the whole subtree, so putting it on the root is enough
    for most tools. Use :func:`add_llms_option` to add it at every level.
    """
    kwargs.setdefault("help", LLMS_HELP)
    return _click.option(
        *(param_decls or ("--llms",)),
        is_flag=True,
        expose_value=False,
        is_eager=True,
        callback=print_llms,
        **kwargs,
    )


def add_llms_option(cmd: Any, *, recursive: bool = True) -> Any:
    """Append ``--llms`` to an already-built command (and its subcommands).

    Works for Typer-built commands too, whose classes come from Typer's
    vendored copy of Click.
    """
    option_cls = _option_class(cmd)
    for node in _iter_commands(cmd) if recursive else [cmd]:
        if any(getattr(p, "name", None) == "llms" for p in node.params):
            continue
        node.params.append(
            option_cls(
                param_decls=["--llms"],
                is_flag=True,
                expose_value=False,
                is_eager=True,
                callback=print_llms,
                help=LLMS_HELP,
            )
        )
    return cmd


def _option_class(cmd: Any) -> Any:
    if type(cmd).__module__.startswith("typer"):
        from typer.core import TyperOption

        return TyperOption
    return _click.Option


def _iter_commands(cmd: Any):
    yield cmd
    for sub in (getattr(cmd, "commands", None) or {}).values():
        yield from _iter_commands(sub)
