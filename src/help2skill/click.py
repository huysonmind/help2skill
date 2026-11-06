"""Click integration: a ``--llms`` flag that prints the Markdown reference."""

from __future__ import annotations

import os
import sys
from typing import Any

# No top-level ``import click``: Typer >= 0.26 vendors Click, so a Typer app may run
# without the ``click`` package installed.
from ._click import from_context
from .render import LLMS_MAX_CHARS, render_llms

LLMS_HELP = "Print a Markdown reference of this command for LLM agents, then exit."
MAX_CHARS_ENV = "HELP2SKILL_LLMS_MAX_CHARS"


def print_llms(ctx: Any, param: Any, value: bool) -> None:
    """Eager option callback usable with Click and Typer-built commands."""
    if not value or ctx.resilient_parsing:
        return
    text = render_llms(
        from_context(ctx), max_chars=_max_chars(), subcommand_flag=_subcommands_have_llms(ctx.command)
    )
    sys.stdout.write(text)
    sys.stdout.flush()
    ctx.exit()


def _subcommands_have_llms(cmd: Any) -> bool:
    subs = list((getattr(cmd, "commands", None) or {}).values())
    return bool(subs) and all(any(getattr(p, "name", None) == "llms" for p in s.params) for s in subs)


def _max_chars() -> int:
    """Output budget for ``--llms``; set the env var to 0 for the full reference."""
    try:
        return int(os.environ.get(MAX_CHARS_ENV, LLMS_MAX_CHARS))
    except ValueError:
        return LLMS_MAX_CHARS


def llms_option(*param_decls: str, **kwargs: Any):
    """Decorator adding ``--llms`` to one Click command or group.

    On a group it prints the whole subtree, so putting it on the root is enough
    for most tools. Use :func:`add_llms_option` to add it at every level.
    """
    import click

    kwargs.setdefault("help", LLMS_HELP)
    return click.option(
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
    import click

    return click.Option


def _iter_commands(cmd: Any):
    yield cmd
    for sub in (getattr(cmd, "commands", None) or {}).values():
        yield from _iter_commands(sub)
