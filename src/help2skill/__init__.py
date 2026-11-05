"""Make Python CLIs ready for LLM agents.

Generate an LLM-friendly reference (``--llms``) and an Agent Skills ``SKILL.md``
straight from a Click, Typer or argparse command tree, and catch drift between
that documentation and the real CLI in CI.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ._argparse import from_argparse
from ._click import from_click, is_click_command
from .model import Command, Param
from .render import default_description, render_markdown, render_skill, usage
from .sync import Problem, check, update_block

__all__ = [
    "Command",
    "Param",
    "Problem",
    "check",
    "check_skill_file",
    "default_description",
    "introspect",
    "render_markdown",
    "render_skill",
    "update_block",
    "usage",
    "write_skill",
]

__version__ = "0.1.0"


def introspect(cli: Any, name: str | None = None) -> Command:
    """Build a :class:`Command` tree from a Click command, Typer app or ArgumentParser.

    ``name`` is the program name users type (e.g. ``"mytool"``); pass it when the
    framework cannot know it, as with Typer apps and ``__main__``-style parsers.
    """
    if isinstance(cli, Command):
        return cli
    if isinstance(cli, argparse.ArgumentParser):
        return from_argparse(cli, name)
    if hasattr(cli, "registered_commands") and hasattr(cli, "registered_groups"):
        import typer.main

        cmd = typer.main.get_command(cli)
        return from_click(cmd, name or getattr(cli.info, "name", None))
    if is_click_command(cli):
        return from_click(cli, name)
    raise TypeError(f"don't know how to introspect {type(cli).__name__}; expected Click, Typer or argparse")


def write_skill(
    cli: Any,
    path: str | Path,
    *,
    name: str,
    description: str | None = None,
    program: str | None = None,
) -> Path:
    """Create ``path`` as a SKILL.md, or refresh only its generated block if it exists.

    ``name`` is the skill name; ``program`` is the command users type and
    defaults to ``name``.
    """
    cmd = introspect(cli, program or name)
    path = Path(path)
    if path.exists():
        text = update_block(path.read_text(encoding="utf-8"), render_markdown(cmd, level=2))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = render_skill(cmd, name=name, description=description or default_description(cmd))
    path.write_text(text, encoding="utf-8")
    return path


def check_skill_file(cli: Any, path: str | Path, *, program: str | None = None) -> list[Problem]:
    """Return drift problems between the SKILL.md at ``path`` and the CLI."""
    text = Path(path).read_text(encoding="utf-8")
    return check(text, introspect(cli, program or _skill_name(text)))


def _skill_name(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'") or None
    return None
