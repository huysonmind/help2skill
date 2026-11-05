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
from ._click import Resolver, default_resolve, from_click, is_click_command
from .model import Command, Param
from .privacy import find_machine_paths, redact_home
from .render import (
    LLMS_MAX_CHARS,
    SKILL_MAX_CHARS,
    default_description,
    render_index,
    render_llms,
    render_markdown,
    render_skill,
    usage,
)
from .sync import REFERENCE_FILE, Problem, check, skill_parts, update_block

__all__ = [
    "Command",
    "Param",
    "Problem",
    "LLMS_MAX_CHARS",
    "REFERENCE_FILE",
    "SKILL_MAX_CHARS",
    "check",
    "check_skill_file",
    "default_description",
    "default_resolve",
    "find_machine_paths",
    "introspect",
    "redact_home",
    "render_index",
    "render_llms",
    "render_markdown",
    "render_skill",
    "update_block",
    "usage",
    "write_skill",
]

__version__ = "0.1.0"


def introspect(cli: Any, name: str | None = None, *, resolve: Resolver | None = None) -> Command:
    """Build a :class:`Command` tree from a Click command, Typer app or ArgumentParser.

    ``name`` is the program name users type (e.g. ``"mytool"``); pass it when the
    framework cannot know it, as with Typer apps and ``__main__``-style parsers.
    ``resolve`` turns lazy placeholder commands into real ones (Click/Typer only);
    see :func:`default_resolve`.
    """
    if isinstance(cli, Command):
        return cli
    if isinstance(cli, argparse.ArgumentParser):
        return from_argparse(cli, name)
    if hasattr(cli, "registered_commands") and hasattr(cli, "registered_groups"):
        import typer.main

        cmd = typer.main.get_command(cli)
        return from_click(cmd, name or getattr(cli.info, "name", None), resolve=resolve)
    if is_click_command(cli):
        return from_click(cli, name, resolve=resolve)
    raise TypeError(f"don't know how to introspect {type(cli).__name__}; expected Click, Typer or argparse")


def write_skill(
    cli: Any,
    path: str | Path,
    *,
    name: str,
    description: str | None = None,
    program: str | None = None,
    max_chars: int = SKILL_MAX_CHARS,
    resolve: Resolver | None = None,
) -> Path:
    """Create ``path`` as a SKILL.md, or refresh only its generated block if it exists.

    ``name`` is the skill name; ``program`` is the command users type and
    defaults to ``name``. When the full reference is longer than ``max_chars``
    (0 = never), SKILL.md gets a command index and the full reference goes to
    ``references/commands.md`` next to it, which agents read on demand.
    Your home directory is replaced by ``~`` in everything written.
    """
    cmd = introspect(cli, program or name, resolve=resolve)
    path = Path(path)
    block, reference = skill_parts(cmd, max_chars=max_chars)
    if path.exists():
        text = update_block(path.read_text(encoding="utf-8"), block)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = render_skill(cmd, name=name, description=description or default_description(cmd), block=block)
    path.write_text(text, encoding="utf-8")
    reference_path = path.parent / REFERENCE_FILE
    if reference is not None:
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_text(reference, encoding="utf-8")
    elif reference_path.exists():
        reference_path.unlink()
    return path


def check_skill_file(
    cli: Any,
    path: str | Path,
    *,
    program: str | None = None,
    max_chars: int = SKILL_MAX_CHARS,
    resolve: Resolver | None = None,
) -> list[Problem]:
    """Return drift problems between the SKILL.md at ``path`` (and its reference file) and the CLI."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    reference_path = path.parent / REFERENCE_FILE
    reference = reference_path.read_text(encoding="utf-8") if reference_path.exists() else None
    cmd = introspect(cli, program or _skill_name(text), resolve=resolve)
    return check(text, cmd, max_chars=max_chars, reference=reference)


def _skill_name(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'") or None
    return None
