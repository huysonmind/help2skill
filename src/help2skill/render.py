"""Render a :class:`Command` tree as Markdown for LLM agents."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .model import Command, Param

if TYPE_CHECKING:
    from .sync import Settings

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Above these sizes output switches to an index (about 5k and 8k tokens).
LLMS_MAX_CHARS = 20_000
SKILL_MAX_CHARS = 30_000


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


def render_markdown(cmd: Command, *, level: int = 1, index: bool = True) -> str:
    """Render ``cmd`` and all its subcommands.

    The root gets a heading at ``level``; every descendant gets ``level + 1``
    with its full path in the heading, so an agent can grep for one command.
    ``index=False`` lists only direct subcommands at the root instead of all.
    Options repeated identically in several commands are listed once.
    """
    shared = _shared_options(cmd)
    root = _section(cmd, level, index=index, shared=shared)
    if shared:
        root += "\n\nShared options (listed by name in the commands that accept them):\n"
        root += "\n".join(shared)
    sections = [root]
    for sub in cmd.walk():
        if sub is not cmd:
            sections.append(_section(sub, level + 1, index=False, shared=shared))
    return "\n\n".join(sections).rstrip() + "\n"


# An option line is listed once when it repeats in this many commands...
SHARED_MIN_COMMANDS = 3
# ...and is at least this long (short lines cost less than the reference to them).
SHARED_MIN_CHARS = 60


def _shared_options(cmd: Command) -> list[str]:
    counts: dict[str, int] = {}
    for node in cmd.walk():
        for line in dict.fromkeys(_param_line(p) for p in node.options):
            counts[line] = counts.get(line, 0) + 1
    return [line for line, n in counts.items() if n >= SHARED_MIN_COMMANDS and len(line) >= SHARED_MIN_CHARS]


def render_index(cmd: Command, *, level: int = 1, hint: str | None = None) -> str:
    """Render only ``cmd`` itself plus an index of every command below it."""
    text = _section(cmd, level, index=True)
    if hint:
        text += f"\n\n{hint}"
    return text + "\n"


def render_llms(cmd: Command, *, max_chars: int = LLMS_MAX_CHARS, subcommand_flag: bool = True) -> str:
    """What ``--llms`` prints: the full reference, or an index when it is too long.

    ``max_chars <= 0`` disables the limit. ``subcommand_flag`` says whether
    subcommands accept ``--llms`` too; the index then points the agent at it,
    otherwise at ``--help``.
    """
    full = render_markdown(cmd)
    if max_chars <= 0 or len(full) <= max_chars or not cmd.is_group:
        return full
    path = " ".join(cmd.path)
    how = f"`{path} <command> --llms`" if subcommand_flag else f"`{path} <command> --help`"
    hint = f"Index only: the full reference is {len(full):,} characters. For one command, run {how}."
    return render_index(cmd, hint=hint)


def render_skill(
    cmd: Command,
    *,
    name: str,
    description: str,
    body: str | None = None,
    block: str | None = None,
    settings: Settings | None = None,
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
    generated = block if block is not None else render_markdown(cmd, level=2)
    return f"{front}\n{intro}{wrap_block(generated, settings)}"


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


def _section(cmd: Command, level: int, *, index: bool, shared: list[str] | None = None) -> str:
    title = f"{'#' * level} `{usage(cmd)}`"
    if cmd.deprecated:
        title += " (deprecated)"
    lines = [title, ""]
    if cmd.aliases:
        lines += ["Aliases: " + ", ".join(f"`{a}`" for a in cmd.aliases), ""]
    if cmd.help:
        lines += [cmd.help, ""]
    if cmd.arguments:
        lines += ["Arguments:", *(_param_line(p) for p in cmd.arguments), ""]
    if cmd.options:
        own, common = [], []
        for p in cmd.options:
            line = _param_line(p)
            if shared and line in shared:
                common.append(_option_names(p))
            else:
                own.append(line)
        lines.append("Options:")
        lines += own
        if common:
            lines.append("- Shared options: " + ", ".join(f"`{c}`" for c in common))
        lines.append("")
    for names, required in cmd.exclusive:
        text = "Mutually exclusive: " + ", ".join(f"`{n}`" for n in names)
        lines += [text + (" (one is required)" if required else ""), ""]
    if cmd.is_group:
        if cmd.default_command:
            prog = " ".join(cmd.path)
            lines += [
                f"Default command: `{cmd.default_command}`. When the first argument is not a command "
                f"name, `{prog} ARGS...` runs `{prog} {cmd.default_command} ARGS...`.",
                "",
            ]
        lines.append("Commands:" if not index else "Commands (all levels):")
        children = [c for c in cmd.walk() if c is not cmd] if index else cmd.subcommands
        defaults = {tuple(node.path + [node.default_command]) for node in cmd.walk() if node.default_command}
        for child in children:
            lines.append(_index_line(child, is_default=tuple(child.path) in defaults))
        lines.append("")
    return "\n".join(lines).rstrip()


def _index_line(cmd: Command, *, is_default: bool = False) -> str:
    flags = []
    if is_default:
        flags.append("default command")
    if cmd.deprecated:
        flags.append("deprecated")
    if cmd.aliases:
        flags.append("aliases: " + ", ".join(cmd.aliases))
    text = f"- `{' '.join(cmd.path)}`"
    if flags:
        text += f" ({'; '.join(flags)})"
    if cmd.short_help:
        text += f": {cmd.short_help}"
    return text


def _param_line(p: Param) -> str:
    sig = _argument_token(p) if not p.is_option else _option_sig(p)
    notes = []
    if not p.is_option:
        notes.append("one of: " + ", ".join(p.choices) if p.choices else p.type)
    if p.range:
        notes.append(f"range: {p.range}")
    if p.case_insensitive:
        notes.append("case-insensitive")
    if p.required:
        notes.append("required")
    if p.count:
        notes.append(f"repeat to increase, e.g. {_repeat_example(p)}")
    elif p.multiple and p.is_option:
        notes.append("repeatable")
    if p.optional_value and not p.is_flag:
        notes.append("value optional")
    if p.default is not None and "default" not in (p.help or "").lower():
        notes.append(f"default: {p.default}")
    if p.envvars:
        notes.append("env: " + ", ".join(p.envvars))
    if p.prompts:
        notes.append("prompts when omitted: pass it explicitly")
    text = f"- `{sig}`"
    if notes:
        text += f" ({'; '.join(notes)})"
    if p.help:
        text += f": {_one_line(p.help)}"
    return text


def _repeat_example(p: Param) -> str:
    short = next((o for o in p.opts if len(o) == 2 and o[0] == "-" and o[1] != "-"), None)
    if short:
        return short + short[1]
    opt = p.opts[0] if p.opts else p.name
    return f"{opt} {opt}"


def _option_names(p: Param) -> str:
    return ", ".join(sorted(p.opts, key=len))


def _option_sig(p: Param) -> str:
    names = _option_names(p)
    if p.secondary_opts:
        names += " / " + ", ".join(sorted(p.secondary_opts, key=len))
    if p.is_flag:
        return names
    return f"{names} {_value_sig(p)}"


def _value_sig(p: Param) -> str:
    if p.value_tokens:
        return " ".join(p.value_tokens)
    hint = _value_hint(p)
    if p.nargs == "?" or p.optional_value:
        return f"[{hint}]"
    if p.nargs == "*":
        return f"[{hint} ...]"
    if p.nargs == "+":
        return f"{hint} [{hint} ...]"
    if p.nargs == "...":
        return f"{hint}..."
    return hint


def _value_hint(p: Param) -> str:
    if p.choices:
        return "[" + "|".join(p.choices) + "]"
    if p.metavar:
        return p.metavar
    return p.type.upper().replace(" ", "_")


def _argument_token(p: Param) -> str:
    if p.value_tokens:
        token = " ".join(p.value_tokens)
    else:
        token = p.metavar or p.name.upper()
        if p.multiple:
            token += "..."
    return token if p.required else f"[{token}]"


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _yaml_str(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
