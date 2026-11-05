"""Render a :class:`Command` tree as Markdown for LLM agents."""

from __future__ import annotations

import re

from .model import Command, Param

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def usage(cmd: Command) -> str:
    """One-line invocation signature, e.g. ``tool db migrate [OPTIONS] NAME``."""
    parts = [" ".join(cmd.path)]
    if cmd.options:
        parts.append("[OPTIONS]")
    for arg in cmd.arguments:
        parts.append(_argument_token(arg))
    if cmd.is_group:
        parts.append("COMMAND [ARGS]...")
    return " ".join(parts)


def render_markdown(cmd: Command, *, level: int = 1) -> str:
    """Render ``cmd`` and all its subcommands.

    The root gets a heading at ``level``; every descendant gets ``level + 1``
    with its full path in the heading, so an agent can grep for one command.
    """
    sections = [_section(cmd, level, index=True)]
    for sub in cmd.walk():
        if sub is not cmd:
            sections.append(_section(sub, level + 1, index=False))
    return "\n\n".join(sections).rstrip() + "\n"


def render_skill(
    cmd: Command,
    *,
    name: str,
    description: str,
    body: str | None = None,
) -> str:
    """Render a complete ``SKILL.md`` (Agent Skills format).

    ``body`` is free-form, hand-written guidance placed before the generated
    reference. The reference sits between markers so it can be regenerated
    without touching the hand-written parts (see :mod:`help2skill.sync`).
    """
    from .sync import wrap_block

    validate_skill_metadata(name, description)
    front = f"---\nname: {name}\ndescription: {_yaml_str(description)}\n---\n"
    intro = body.strip() + "\n\n" if body else ""
    return f"{front}\n{intro}{wrap_block(render_markdown(cmd, level=2))}"


def default_description(cmd: Command) -> str:
    summary = cmd.short_help or (cmd.help or "").split("\n\n")[0].replace("\n", " ")
    text = f"Use the `{cmd.name}` command-line tool."
    if summary:
        text += f" {summary.rstrip('.')}."
    return text[:1024]


def validate_skill_metadata(name: str, description: str) -> None:
    if not (1 <= len(name) <= 64) or not SKILL_NAME_RE.match(name):
        raise ValueError(
            f"invalid skill name {name!r}: use 1-64 lowercase letters, digits and single hyphens"
        )
    if not description.strip():
        raise ValueError("skill description must not be empty")
    if len(description) > 1024:
        raise ValueError("skill description must be at most 1024 characters")
    if "<" in description or ">" in description:
        raise ValueError("skill description must not contain angle brackets")


def _section(cmd: Command, level: int, *, index: bool) -> str:
    title = f"{'#' * level} `{usage(cmd)}`"
    if cmd.deprecated:
        title += " (deprecated)"
    lines = [title, ""]
    if cmd.help:
        lines += [cmd.help, ""]
    if cmd.arguments:
        lines += ["Arguments:", *(_param_line(p) for p in cmd.arguments), ""]
    if cmd.options:
        lines += ["Options:", *(_param_line(p) for p in cmd.options), ""]
    if cmd.is_group:
        lines.append("Commands:" if not index else "Commands (all levels):")
        children = [c for c in cmd.walk() if c is not cmd] if index else cmd.subcommands
        for child in children:
            summary = f": {child.short_help}" if child.short_help else ""
            flag = " (deprecated)" if child.deprecated else ""
            lines.append(f"- `{' '.join(child.path)}`{flag}{summary}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _param_line(p: Param) -> str:
    sig = _argument_token(p) if not p.is_option else _option_sig(p)
    notes = []
    if not p.is_option:
        notes.append(p.type)
    if p.required:
        notes.append("required")
    if p.multiple and p.is_option:
        notes.append("repeatable")
    if p.default is not None:
        notes.append(f"default: {p.default}")
    if p.envvars:
        notes.append("env: " + ", ".join(p.envvars))
    text = f"- `{sig}`"
    if notes:
        text += f" ({'; '.join(notes)})"
    if p.help:
        text += f": {_one_line(p.help)}"
    return text


def _option_sig(p: Param) -> str:
    names = ", ".join(sorted(p.opts, key=len))
    if p.secondary_opts:
        names += " / " + ", ".join(sorted(p.secondary_opts, key=len))
    if p.is_flag:
        return names
    return f"{names} {_value_hint(p)}"


def _value_hint(p: Param) -> str:
    if p.choices:
        return "[" + "|".join(p.choices) + "]"
    if p.metavar:
        return p.metavar
    return p.type.upper().replace(" ", "_")


def _argument_token(p: Param) -> str:
    token = p.metavar or p.name.upper()
    if p.multiple:
        token += "..."
    return token if p.required else f"[{token}]"


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _yaml_str(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
