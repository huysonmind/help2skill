"""Introspect plumbum ``cli.Application`` classes."""

from __future__ import annotations

import inspect
from typing import Any

from .model import Command, Param


def is_plumbum_app(obj: Any) -> bool:
    if not inspect.isclass(obj):
        return False
    return any(
        base.__module__.startswith("plumbum.cli") and base.__name__ == "Application" for base in obj.__mro__
    )


def from_plumbum(app_cls: Any, name: str | None = None) -> Command:
    """Build a :class:`Command` tree from a plumbum Application subclass."""
    root_name = name or _progname(app_cls) or app_cls.__name__.lower()
    return _build(app_cls, root_name, [root_name])


def _progname(app_cls: Any) -> str | None:
    prog = getattr(app_cls, "PROGNAME", None)
    return str(prog) if isinstance(prog, str) and prog else None


def _build(app_cls: Any, name: str, path: list[str]) -> Command:
    app = app_cls(" ".join(path))
    subcommands = []
    for sub_name in sorted(app._subcommands):
        sub_cls = app._subcommands[sub_name].get()
        subcommands.append(_build(sub_cls, sub_name, path + [sub_name]))
    description = getattr(app_cls, "DESCRIPTION", None) or inspect.getdoc(app_cls)
    help_text = inspect.cleandoc(description) if description else None
    return Command(
        name=name,
        path=path,
        help=help_text,
        short_help=help_text.split("\n\n")[0].replace("\n", " ") if help_text else None,
        params=_switches(app) + _positionals(app_cls),
        subcommands=subcommands,
    )


def _is_meta(func: Any) -> bool:
    """help, help-all, version and completions come from ``Application`` itself."""
    return getattr(func, "__qualname__", "").startswith("Application.")


def _switches(app: Any) -> list[Param]:
    params = []
    for func, info in app._switches_by_func.items():
        if _is_meta(func):
            continue
        # A switch can lose a name to a later one (``-v`` for --verbose over --version).
        names = [n for n in info.names if app._switches_by_name.get(n) is info]
        if not names:
            continue
        opts = sorted((f"-{n}" if len(n) == 1 else f"--{n}" for n in names), key=len)
        argtype = info.argtype
        count = type(func).__name__ == "CountOf"
        is_flag = argtype is None
        param = Param(
            name=getattr(func, "__name__", None) or names[-1].replace("-", "_"),
            kind="option",
            opts=opts,
            type="bool" if is_flag and not count else _type_name(argtype),
            choices=_choices(argtype),
            required=bool(info.mandatory),
            default=None if is_flag else _default(func),
            is_flag=is_flag,
            multiple=bool(info.list),
            envvars=[info.envname] if info.envname else [],
            help=_help(info.help),
            metavar=info.argname if info.argname and info.argname != "VALUE" else None,
            count=count,
            range=_range(argtype),
            case_insensitive=_choices(argtype) is not None and not getattr(argtype, "case_sensitive", True),
        )
        params.append(param)
    return sorted(params, key=lambda p: p.opts[-1])


def _positionals(app_cls: Any) -> list[Param]:
    main = getattr(app_cls, "main", None)
    if main is None or _is_meta(main):
        return []
    spec = inspect.getfullargspec(main)
    try:
        annotations = inspect.get_annotations(main, eval_str=True)
    except Exception:  # names only resolvable where the class was defined
        annotations = dict(spec.annotations)
    names = spec.args[1:]
    defaults = spec.defaults or ()
    optional_from = len(names) - len(defaults)
    params = []
    for index, arg in enumerate(names):
        annotation = annotations.get(arg)
        default = defaults[index - optional_from] if index >= optional_from else None
        params.append(
            Param(
                name=arg,
                kind="argument",
                opts=[arg],
                type=_type_name(annotation),
                choices=_choices(annotation),
                required=index < optional_from,
                default=None if default is None else str(default),
                range=_range(annotation),
            )
        )
    if spec.varargs:
        annotation = annotations.get(spec.varargs)
        params.append(
            Param(
                name=spec.varargs,
                kind="argument",
                opts=[spec.varargs],
                type=_type_name(annotation),
                multiple=True,
                nargs=-1,
            )
        )
    return params


# plumbum's help when none is given.
_PLACEHOLDER_HELP = frozenset({"Sets an attribute"})


def _help(text: str | None) -> str | None:
    text = (text or "").strip()
    return None if not text or text in _PLACEHOLDER_HELP else text


def _default(func: Any) -> str | None:
    value = getattr(func, "_default_value", None)
    if value is None or value == [] or value == "":
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _choices(argtype: Any) -> list[str] | None:
    values = getattr(argtype, "values", None)
    if type(argtype).__name__ != "Set" or not values:
        return None
    return [v if isinstance(v, str) else getattr(v, "__name__", str(v)) for v in values]


def _range(argtype: Any) -> str | None:
    if type(argtype).__name__ != "Range":
        return None
    return f"{argtype.start}<=x<={argtype.end}"


def _type_name(argtype: Any) -> str:
    if argtype is None or argtype is str:
        return "text"
    if isinstance(argtype, str):  # unevaluated annotation, e.g. "cli.ExistingFile"
        name = argtype.rsplit(".", 1)[-1]
        if name.endswith(("File", "Path", "Directory")):
            return "path"
        return {"str": "text"}.get(name, name.lower())
    kind = type(argtype).__name__
    if kind == "Set":
        return "text"
    if kind == "Range":
        return "int"
    if kind == "Predicate":
        name = getattr(argtype.func, "__name__", "text")
        return "path" if name.endswith(("File", "Path", "Directory")) else name.lower()
    name = getattr(argtype, "__name__", kind)
    return {"Path": "path", "LocalPath": "path"}.get(name, name.lower())
