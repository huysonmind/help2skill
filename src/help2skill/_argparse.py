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
)
_MULTI_ACTIONS = (argparse._AppendAction, argparse._ExtendAction, argparse._AppendConstAction)


def from_argparse(parser: argparse.ArgumentParser, name: str | None = None) -> Command:
    root_name = name or parser.prog
    return _build(parser, root_name, [root_name], help_text=None)


def _build(parser: argparse.ArgumentParser, name: str, path: list[str], help_text: str | None) -> Command:
    params: list[Param] = []
    subcommands: list[Command] = []
    for action in parser._actions:
        if isinstance(action, (argparse._HelpAction, argparse._VersionAction)):
            continue
        if isinstance(action, argparse._SubParsersAction):
            helps = {a.dest: a.help for a in action._choices_actions}
            seen: set[int] = set()
            for sub_name, sub_parser in action.choices.items():
                if id(sub_parser) in seen:  # aliases point at the same parser
                    continue
                seen.add(id(sub_parser))
                subcommands.append(_build(sub_parser, sub_name, path + [sub_name], helps.get(sub_name)))
            continue
        if action.help == argparse.SUPPRESS:
            continue
        params.append(_param(action))
    description = parser.description or help_text
    return Command(
        name=name,
        path=path,
        help=_clean(description),
        short_help=_clean(help_text) or _first_line(description),
        params=params,
        subcommands=subcommands,
    )


def _param(action: argparse.Action) -> Param:
    is_option = bool(action.option_strings)
    is_flag = isinstance(action, _FLAG_ACTIONS) or action.nargs == 0
    multiple = isinstance(action, _MULTI_ACTIONS) or action.nargs in ("*", "+", argparse.REMAINDER)
    required = action.required if is_option else action.nargs not in ("?", "*", argparse.REMAINDER)
    return Param(
        name=action.dest,
        kind="option" if is_option else "argument",
        opts=list(action.option_strings) if is_option else [action.dest],
        type="bool" if is_flag else _type_name(action.type),
        choices=[str(c) for c in action.choices] if action.choices else None,
        required=bool(required),
        default=_default(action, is_flag),
        is_flag=is_flag,
        multiple=multiple,
        nargs=action.nargs if action.nargs is not None else 1,
        help=_clean(_expand_help(action)),
        metavar=_metavar(action),
    )


def _type_name(t: Any) -> str:
    if t is None or t is str:
        return "text"
    return getattr(t, "__name__", type(t).__name__)


def _default(action: argparse.Action, is_flag: bool) -> str | None:
    value = action.default
    if value is None or value == argparse.SUPPRESS or value == "" or value == []:
        return None
    if is_flag and isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _metavar(action: argparse.Action) -> str | None:
    if isinstance(action.metavar, str):
        return action.metavar
    return None


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
