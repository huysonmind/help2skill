"""Introspect ``argparse.ArgumentParser`` trees."""

from __future__ import annotations

import argparse
from typing import Any

from .model import Command, Param

_FLAG_ACTIONS = (
    argparse._StoreTrueAction,
    argparse._StoreFalseAction,
    argparse._StoreConstAction,
    argparse._CountAction,
    argparse._AppendConstAction,
)
# The option itself may be repeated.
_REPEAT_ACTIONS = (
    argparse._AppendAction,
    argparse._ExtendAction,
    argparse._AppendConstAction,
    argparse._CountAction,
)


def from_argparse(parser: argparse.ArgumentParser, name: str | None = None) -> Command:
    root_name = name or parser.prog
    return _build(parser, root_name, [root_name], help_text=None)


def _build(parser: argparse.ArgumentParser, name: str, path: list[str], help_text: str | None) -> Command:
    params: list[Param] = []
    hidden_params: list[Param] = []
    subcommands: list[Command] = []
    aliases_of: dict[str, list[str]] = {}
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        if isinstance(action, argparse._SubParsersAction):
            helps = {a.dest: a.help for a in action._choices_actions}
            primary: dict[int, str] = {}
            for sub_name, sub_parser in action.choices.items():
                if id(sub_parser) in primary:  # aliases point at the same parser
                    aliases_of.setdefault(primary[id(sub_parser)], []).append(sub_name)
                    continue
                primary[id(sub_parser)] = sub_name
                subcommands.append(_build(sub_parser, sub_name, path + [sub_name], helps.get(sub_name)))
            continue
        if action.help == argparse.SUPPRESS:
            if action.option_strings:
                hidden_params.append(_param(action))
            continue
        params.append(_param(action))
    for sub in subcommands:
        sub.aliases = aliases_of.get(sub.name, [])
    description = parser.description or help_text
    full_help = _clean(description)
    if parser.epilog and parser.epilog != argparse.SUPPRESS:
        epilog = parser.epilog.strip()
        full_help = f"{full_help}\n\n{epilog}" if full_help else epilog
    return Command(
        name=name,
        path=path,
        help=full_help,
        short_help=_clean(help_text) or _first_line(description),
        params=params,
        subcommands=subcommands,
        exclusive=_exclusive_groups(parser),
        hidden_params=hidden_params,
    )


def _exclusive_groups(parser: argparse.ArgumentParser) -> list[tuple[list[str], bool]]:
    groups = []
    for group in parser._mutually_exclusive_groups:
        names = [
            max(a.option_strings, key=len) if a.option_strings else a.dest.upper()
            for a in group._group_actions
            if a.help != argparse.SUPPRESS
        ]
        if len(names) > 1:
            groups.append((names, bool(group.required)))
    return groups


def _param(action: argparse.Action) -> Param:
    is_option = bool(action.option_strings)
    is_flag = isinstance(action, _FLAG_ACTIONS) or action.nargs == 0
    nargs = action.nargs if action.nargs is not None else 1
    if is_option:
        multiple = isinstance(action, _REPEAT_ACTIONS)
        required = action.required
    else:
        multiple = nargs in ("*", "+", argparse.REMAINDER) or (isinstance(nargs, int) and nargs > 1)
        required = nargs not in ("?", "*", argparse.REMAINDER)
    return Param(
        name=action.dest,
        kind="option" if is_option else "argument",
        opts=list(action.option_strings) if is_option else [action.dest],
        type="bool" if is_flag else _type_name(action.type),
        choices=[str(c) for c in action.choices]
        if action.choices and not _is_range(action.choices)
        else None,
        required=bool(required),
        default=_default(action, is_flag),
        is_flag=is_flag,
        multiple=multiple,
        nargs=nargs,
        help=_clean(_expand_help(action)),
        metavar=action.metavar if isinstance(action.metavar, str) else None,
        value_tokens=None if is_flag else _value_tokens(action, nargs),
        count=isinstance(action, argparse._CountAction),
        range=_range_text(action.choices),
        optional_value=is_option and nargs == "?",
    )


def _value_tokens(action: argparse.Action, nargs: Any) -> list[str] | None:
    """Tokens for options that take a fixed number (> 1) of values."""
    if not action.option_strings or not isinstance(nargs, int) or nargs <= 1:
        return None
    if isinstance(action.metavar, tuple) and len(action.metavar) == nargs:
        return list(action.metavar)
    token = action.metavar if isinstance(action.metavar, str) else _type_name(action.type).upper()
    return [token] * nargs


def _is_range(choices: Any) -> bool:
    return isinstance(choices, range) and len(choices) > 20


def _range_text(choices: Any) -> str | None:
    if not isinstance(choices, range) or not _is_range(choices) or choices.step != 1:
        return None
    return f"{choices.start}<=x<={choices.stop - 1}"


def _type_name(t: Any) -> str:
    if t is None or t is str:
        return "text"
    name = getattr(t, "__name__", type(t).__name__)
    return {"PurePath": "path", "Path": "path", "FileType": "file"}.get(name, name.lower())


def _default(action: argparse.Action, is_flag: bool) -> str | None:
    value = action.default
    if value is None or value == argparse.SUPPRESS or value == "" or value == []:
        return None
    if is_flag and isinstance(
        action, (argparse._StoreTrueAction, argparse._StoreFalseAction, argparse._CountAction)
    ):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _expand_help(action: argparse.Action) -> str | None:
    text = action.help
    if not text or "%" not in text:
        return text
    try:
        return text % {**vars(action), "prog": "", "default": action.default}
    except (KeyError, TypeError, ValueError):
        return text


def _first_line(text: str | None) -> str | None:
    if not text:
        return None
    return text.strip().split("\n\n")[0].replace("\n", " ") or None


def _clean(text: str | None) -> str | None:
    return text.strip() if text and text.strip() else None
