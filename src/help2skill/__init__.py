"""Make Python CLIs ready for LLM agents.

Generate an LLM-friendly reference (``--llms``) and an Agent Skills ``SKILL.md``
straight from a Click, Typer or argparse command tree, and catch drift between
that documentation and the real CLI in CI.
"""

from __future__ import annotations

import argparse
import inspect
import re
from pathlib import Path
from typing import Any

from ._argparse import from_argparse
from ._click import Resolver, default_resolve, from_click, is_click_command
from ._cyclopts import from_cyclopts, is_cyclopts_app
from ._plumbum import from_plumbum, is_plumbum_app
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
from .sync import REFERENCE_FILE, Problem, Settings, check, read_settings, skill_parts, update_block

__all__ = [
    "Command",
    "Param",
    "Problem",
    "Settings",
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
    "read_settings",
    "render_skill",
    "update_block",
    "usage",
    "write_skill",
]

__version__ = "0.2.0"


# Names a framework falls back to when the real program name is unknown.
GENERIC_NAMES = frozenset(
    {"cli", "main", "app", "run", "entry", "entrypoint", "command", "__main__", "__main__.py", "-c"}
)
UNNAMED = "__help2skill_unnamed__"


def introspect(
    cli: Any,
    name: str | None = None,
    *,
    resolve: Resolver | None = None,
    hide_defaults: list[str] | None = None,
) -> Command:
    """Build a :class:`Command` tree from a Click command, Typer app or ArgumentParser.

    ``name`` is the program name users type (e.g. ``"mytool"``); pass it when the
    framework cannot know it, as with Typer apps and ``__main__``-style parsers.
    ``resolve`` turns lazy placeholder commands into real ones (Click/Typer only);
    see :func:`default_resolve`. ``hide_defaults`` lists parameters (by name or
    option string) whose default is computed at run time and must not be written.
    """
    cmd = _introspect(cli, name, resolve)
    if hide_defaults:
        _hide_defaults(cmd, hide_defaults)
    return cmd


def _introspect(cli: Any, name: str | None, resolve: Resolver | None) -> Command:
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
    if is_cyclopts_app(cli):
        return from_cyclopts(cli, name)
    if is_plumbum_app(cli):
        return from_plumbum(cli, name)
    if inspect.isfunction(cli):
        raise TypeError(
            f"{getattr(cli, '__name__', cli)!r} is a function, not a CLI; if it builds the "
            "parser, pass its result (e.g. build_parser()) instead"
        )
    raise TypeError(
        f"don't know how to introspect {type(cli).__name__}; "
        "expected Click, Typer, argparse, cyclopts or plumbum"
    )


def _hide_defaults(cmd: Command, names: list[str]) -> None:
    wanted = set(names)
    found: set[str] = set()
    for node in cmd.walk():
        for p in node.params:
            hits = wanted & {p.name, *p.opts, *p.secondary_opts}
            if hits:
                if p.default and p.help:
                    # argparse help often embeds the value: "(default: %(default)s)".
                    pattern = r"(default:?\s*)" + re.escape(p.default)
                    p.help = re.sub(pattern, r"\1computed at run time", p.help, flags=re.I)
                p.default = None
                found |= hits
    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"--hide-default: no parameter named {', '.join(missing)}")


def program_name(cli: Any, *candidates: str | None, resolve: Resolver | None = None) -> str | None:
    """First usable program name: the candidates in order, then the CLI's own name.

    Generic names such as ``cli`` or ``main`` (a function name, not what users
    type) are skipped. Returns ``None`` when nothing better is known.
    """
    for candidate in candidates:
        if candidate:
            return candidate
    own = _introspect(cli, None, resolve).name
    return None if own in GENERIC_NAMES or own == UNNAMED else own


def write_skill(
    cli: Any,
    path: str | Path,
    *,
    name: str | None = None,
    description: str | None = None,
    program: str | None = None,
    max_chars: int | None = None,
    resolve: Resolver | None = None,
    hide_defaults: list[str] | None = None,
) -> Path:
    """Create ``path`` as a SKILL.md, or refresh only its generated block if it exists.

    ``name`` is the skill name (needed only to create the file). ``program`` is
    the command users type; it defaults to the value stored in the file, then
    the CLI's own name, then ``name``. When the full reference is longer than
    ``max_chars`` (default 30,000; 0 = never), SKILL.md gets a command index and
    the full reference goes to ``references/commands.md`` next to it, which
    agents read on demand. Your home directory is replaced by ``~``.

    The settings used are stored in the block's begin marker, so a refresh or
    a check needs none of them again.
    """
    path = Path(path)
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    stored = read_settings(existing) if existing else Settings()
    skill_name = name or (_skill_name(existing) if existing else None)
    if not skill_name:
        raise ValueError(f"{path} does not exist yet: pass a skill name to create it")
    settings = Settings(
        program=program_name(cli, program, stored.program, resolve=resolve) or skill_name,
        max_chars=max_chars
        if max_chars is not None
        else (stored.max_chars if stored.max_chars is not None else SKILL_MAX_CHARS),
        hide_defaults=hide_defaults if hide_defaults is not None else stored.hide_defaults,
    )
    cmd = introspect(cli, settings.program, resolve=resolve, hide_defaults=settings.hide_defaults)
    assert settings.max_chars is not None
    block, reference = skill_parts(cmd, max_chars=settings.max_chars)
    if existing is not None:
        text = update_block(existing, block, settings)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = render_skill(
            cmd,
            name=skill_name,
            description=description or default_description(cmd),
            block=block,
            settings=settings,
        )
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
    max_chars: int | None = None,
    resolve: Resolver | None = None,
    hide_defaults: list[str] | None = None,
    scripts: tuple[str, ...] = (),
) -> list[Problem]:
    """Return drift problems between the SKILL.md at ``path`` (and its reference file) and the CLI.

    Settings not passed are read from the file's generated block. ``scripts`` are
    file names that also run the CLI in examples (``python scripts/tool.py …``).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found (relative paths start from the current directory, {Path.cwd()})"
        )
    text = path.read_text(encoding="utf-8")
    stored = read_settings(text)
    reference_path = path.parent / REFERENCE_FILE
    reference = reference_path.read_text(encoding="utf-8") if reference_path.exists() else None
    prog = program_name(cli, program, stored.program, resolve=resolve) or _skill_name(text)
    cmd = introspect(
        cli,
        prog,
        resolve=resolve,
        hide_defaults=hide_defaults if hide_defaults is not None else stored.hide_defaults,
    )
    limit = (
        max_chars
        if max_chars is not None
        else (stored.max_chars if stored.max_chars is not None else SKILL_MAX_CHARS)
    )
    return check(text, cmd, max_chars=limit, reference=reference, scripts=scripts)


def _skill_name(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'") or None
    return None
