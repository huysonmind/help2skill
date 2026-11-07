"""Introspect cyclopts ``App`` objects (cyclopts >= 3)."""

from __future__ import annotations

import enum
import inspect
import typing
from typing import Any

from .model import Command, Param

_META_NAMES = frozenset({"--help", "-h", "--version"})
_SEQUENCES = (list, tuple, set, frozenset)


def is_cyclopts_app(obj: Any) -> bool:
    return type(obj).__module__.startswith("cyclopts") and hasattr(obj, "_commands")


def from_cyclopts(app: Any, name: str | None = None) -> Command:
    """Build a :class:`Command` tree from a cyclopts App."""
    root_name = name or _first_name(app) or "cli"
    return _build(app, root_name, [root_name])


def _first_name(app: Any) -> str | None:
    names = getattr(app, "name", None)
    if isinstance(names, str):
        return names
    return names[0] if names else None


def _build(app: Any, name: str, path: list[str]) -> Command:
    by_id: dict[int, list[str]] = {}
    apps: dict[int, Any] = {}
    for cmd_name, sub in app._commands.items():
        if cmd_name in _META_NAMES:
            continue
        sub = _resolve(sub)
        if sub is None:
            continue
        by_id.setdefault(id(sub), []).append(cmd_name)
        apps[id(sub)] = sub
    subcommands = []
    hidden = []
    for key, names in by_id.items():
        sub = apps[key]
        primary = names[0]
        if getattr(sub, "show", True) is False:
            hidden.extend(names)
            continue
        cmd = _build(sub, primary, path + [primary])
        cmd.aliases = names[1:]
        subcommands.append(cmd)
    subcommands.sort(key=lambda c: c.name)
    help_text, short_help = _help(app)
    return Command(
        name=name,
        path=path,
        help=help_text,
        short_help=short_help,
        params=_params(app),
        subcommands=subcommands,
        hidden_subcommands=sorted(hidden),
    )


def _resolve(sub: Any) -> Any:
    """Lazy commands (``CommandSpec``) are resolved to their App."""
    if hasattr(sub, "_commands"):
        return sub
    for attr in ("resolve", "load"):
        method = getattr(sub, attr, None)
        if callable(method):
            try:
                resolved = method()
            except TypeError:
                continue
            if hasattr(resolved, "_commands"):
                return resolved
    return None


def _help(app: Any) -> tuple[str | None, str | None]:
    raw = getattr(app, "help", None)
    if not isinstance(raw, str) or not raw.strip():
        return None, None
    try:
        import docstring_parser  # type: ignore[import-not-found]  # ships with cyclopts

        doc = docstring_parser.parse(raw)
        parts = [p.strip() for p in (doc.short_description, doc.long_description) if p and p.strip()]
        text = "\n\n".join(parts) or None
    except Exception:  # pragma: no cover - docstring_parser always ships with cyclopts
        text = inspect.cleandoc(raw)
    short = text.split("\n\n")[0].replace("\n", " ") if text else None
    return text, short


def _params(app: Any) -> list[Param]:
    if getattr(app, "default_command", None) is None:
        return []
    params = []
    for arg in app.assemble_argument_collection(parse_docstring=True):
        if (
            getattr(arg, "children", None)
            or not getattr(arg, "parse", True)
            or not getattr(arg, "show", True)
        ):
            continue
        param = _param(arg)
        if param is not None:
            params.append(param)
    return params


def _param(arg: Any) -> Param | None:
    kind = arg.field_info.kind
    positional = kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.VAR_POSITIONAL,
    )
    hint, multiple = _unwrap(arg.hint)
    if kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
        multiple = True
    negatives = list(getattr(arg, "negatives", ()) or ())
    names = [n for n in arg.names if n not in negatives]
    # cyclopts parses a bool that may be positional as a flag too (``--verbose``);
    # the flag is how people write it.
    is_flag = hint is bool and not multiple and kind != inspect.Parameter.VAR_POSITIONAL
    if is_flag:
        positional = False
    name = arg.field_info.name if hasattr(arg.field_info, "name") else names[0].lstrip("-")
    env = arg.parameter.env_var or ()
    return Param(
        name=name,
        kind="argument" if positional else "option",
        opts=[name] if positional else sorted(names, key=len),
        secondary_opts=negatives if is_flag else [],
        type="bool" if is_flag else _type_name(hint),
        choices=_choices(hint),
        required=bool(arg.required),
        default=_default(arg.field_info.default, is_flag, bool(negatives)),
        is_flag=is_flag,
        multiple=multiple,
        nargs=-1 if multiple and positional else 1,
        envvars=[env] if isinstance(env, str) else list(env),
        help=(arg.parameter.help or "").strip() or None,
    )


def _unwrap(hint: Any) -> tuple[Any, bool]:
    """Strip Optional/Annotated; report whether the hint is a sequence."""
    multiple = False
    for _ in range(5):
        origin = typing.get_origin(hint)
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        if origin is typing.Annotated:
            hint = args[0]
        elif origin in _SEQUENCES:
            multiple = True
            hint = args[0] if args else str
        elif origin is not None and origin is not typing.Literal and len(args) == 1:
            hint = args[0]  # Optional[X] / X | None
        else:
            break
    return hint, multiple


def _enum_token(member: enum.Enum) -> str:
    # cyclopts' default name_transform: lowercase, "_" -> "-".
    return member.name.lower().replace("_", "-")


def _choices(hint: Any) -> list[str] | None:
    if inspect.isclass(hint) and issubclass(hint, enum.Enum):
        return [_enum_token(m) for m in hint]
    if typing.get_origin(hint) is typing.Literal:
        return [str(v) for v in typing.get_args(hint)]
    return None


def _type_name(hint: Any) -> str:
    if hint is str or hint is inspect.Parameter.empty or _choices(hint) is not None:
        return "text"
    name = getattr(hint, "__name__", None) or str(hint)
    return {"Path": "path", "PurePath": "path"}.get(name, name.lower())


def _default(value: Any, is_flag: bool, has_negative: bool) -> str | None:
    if value is inspect.Parameter.empty or value is None or value == "" or value == [] or value == ():
        return None
    if isinstance(value, bool):
        if is_flag and not value and not has_negative:
            return None
        return "true" if value else "false"
    if isinstance(value, enum.Enum):
        return _enum_token(value)
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)
