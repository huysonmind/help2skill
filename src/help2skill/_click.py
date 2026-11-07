"""Introspect Click commands, including Typer's vendored Click (Typer >= 0.26).

Everything here is duck-typed: Typer's command classes do not subclass
``click.Command`` any more, so ``isinstance`` checks would silently miss them.
"""

from __future__ import annotations

import enum
import inspect
import re
from collections.abc import Callable
from typing import Any

from .model import Command, Param

# Click marks deprecated commands in their help text; the renderer marks them itself.
_DEPRECATED_RE = re.compile(r"\s*\(deprecated(?::[^)]*)?\)\s*", re.I)

# Parameters that exist for the human shell, not for the agent.
INTERNAL_PARAMS = frozenset({"help", "install_completion", "show_completion", "llms"})

# Type names differ between Click versions ("integer range", "int_range"...);
# normalise them so the output is the same everywhere.
_TYPE_NAMES = {
    "str": "text",
    "string": "text",
    "integer": "int",
    "boolean": "bool",
    "filename": "file",
    "unprocessed": "text",
}


Resolver = Callable[[Any], Any]


def default_resolve(cmd: Any) -> Any:
    """Load placeholder commands that only build their real command on demand.

    Covers placeholders with a ``materialize()`` method (Hugging Face's ``hf``).
    Click's documented ``LazyGroup`` pattern needs nothing: it resolves in
    ``get_command``. Pass your own ``resolve`` for other patterns.
    """
    materialize = getattr(cmd, "materialize", None)
    return materialize() if callable(materialize) else cmd


def is_click_command(obj: Any) -> bool:
    return hasattr(obj, "params") and hasattr(obj, "make_context")


def from_click(
    cmd: Any,
    name: str | None = None,
    *,
    parent_ctx: Any = None,
    resolve: Resolver | None = None,
) -> Command:
    """Build a :class:`Command` tree from a Click (or Typer-built) command."""
    resolve = resolve or default_resolve
    cmd = resolve(cmd)
    info_name = name or cmd.name or "cli"
    ctx = _make_context(cmd, info_name, parent_ctx)
    path = (_ctx_path(parent_ctx) if parent_ctx is not None else []) + [info_name]
    return _build(cmd, info_name, path, ctx, resolve)


def from_context(ctx: Any, resolve: Resolver | None = None) -> Command:
    """Build the tree for the command a live Click context is running."""
    path = _ctx_path(ctx)
    return _build(ctx.command, path[-1], path, ctx, resolve or default_resolve)


def _build(cmd: Any, name: str, path: list[str], ctx: Any, resolve: Resolver) -> Command:
    subcommands = []
    hidden = []
    # Sorted: Click sorts, recent Typer keeps definition order; sorting keeps the
    # output identical across versions.
    for sub_name in sorted(_list_commands(cmd, ctx)):
        sub = _get_command(cmd, ctx, sub_name)
        if sub is None:
            continue
        if getattr(sub, "hidden", False):
            hidden.append(sub_name)
            continue
        sub = resolve(sub)
        sub_ctx = _make_context(sub, sub_name, ctx)
        subcommands.append(_build(sub, sub_name, path + [sub_name], sub_ctx, resolve))
    help_text = _clean(getattr(cmd, "help", None), strip_deprecated=True)
    epilog = _clean(getattr(cmd, "epilog", None))
    if epilog:
        help_text = f"{help_text}\n\n{epilog}" if help_text else epilog
    return Command(
        name=name,
        path=path,
        help=help_text,
        short_help=_short_help(cmd),
        params=[_param(p) for p in cmd.params if _visible(p)],
        subcommands=subcommands,
        deprecated=bool(getattr(cmd, "deprecated", False)),
        default_command=getattr(cmd, "default_cmd_name", None),
        hidden_subcommands=hidden,
        passthrough=bool((getattr(cmd, "context_settings", None) or {}).get("ignore_unknown_options")),
    )


def _make_context(cmd: Any, info_name: str, parent: Any) -> Any:
    ctx_class = getattr(cmd, "context_class", None)
    if ctx_class is None:
        return None
    try:
        return ctx_class(cmd, info_name=info_name, parent=parent)
    except Exception:  # pragma: no cover - exotic custom contexts
        return None


def _ctx_path(ctx: Any) -> list[str]:
    parts = []
    while ctx is not None:
        parts.append(ctx.info_name or ctx.command.name or "cli")
        ctx = ctx.parent
    return parts[::-1]


def _list_commands(cmd: Any, ctx: Any) -> list[str]:
    if hasattr(cmd, "list_commands") and ctx is not None:
        return list(cmd.list_commands(ctx))
    return list(getattr(cmd, "commands", {}) or {})


def _get_command(cmd: Any, ctx: Any, name: str) -> Any:
    if hasattr(cmd, "get_command") and ctx is not None:
        return cmd.get_command(ctx, name)
    return (getattr(cmd, "commands", {}) or {}).get(name)


def _visible(p: Any) -> bool:
    return not getattr(p, "hidden", False) and p.name not in INTERNAL_PARAMS


def _param(p: Any) -> Param:
    kind = "option" if p.param_type_name == "option" else "argument"
    ptype = p.type
    count = bool(getattr(p, "count", False))
    is_flag = bool(getattr(p, "is_flag", False)) or count
    envvar = getattr(p, "envvar", None)
    nargs = p.nargs
    value_tokens = None
    if not is_flag:
        if _is_tuple(ptype):
            value_tokens = [_value_token(t) for t in ptype.types]
        elif isinstance(nargs, int) and nargs > 1:
            value_tokens = [_value_token(ptype)] * nargs
    choices = getattr(ptype, "choices", None)
    return Param(
        name=p.name or "",
        kind=kind,
        opts=list(p.opts),
        secondary_opts=list(getattr(p, "secondary_opts", []) or []),
        type="bool" if is_flag and not count else type_name(ptype),
        choices=[str(_plain(c)) for c in choices] if choices and not count else None,
        required=bool(p.required),
        default=None if count else _default(p, is_flag),
        is_flag=is_flag,
        multiple=bool(getattr(p, "multiple", False)) or nargs == -1 or count,
        nargs=nargs,
        envvars=[envvar] if isinstance(envvar, str) else list(envvar or []),
        help=_clean(getattr(p, "help", None)),
        metavar=p.metavar,
        value_tokens=value_tokens,
        count=count,
        range=None if count else _range(ptype),
        case_insensitive=choices is not None and getattr(ptype, "case_sensitive", True) is False,
        prompts=bool(getattr(p, "prompt", None)),
        optional_value=bool(getattr(p, "_flag_needs_value", False)),
    )


def type_name(ptype: Any) -> str:
    """Stable, lowercase name of a Click parameter type."""
    name = str(getattr(ptype, "name", None) or type(ptype).__name__).lower()
    name = name.replace("_", " ")
    if name.endswith(" range"):
        name = name[: -len(" range")]
    return _TYPE_NAMES.get(name, name).replace(" ", "_")


def _is_tuple(ptype: Any) -> bool:
    return isinstance(getattr(ptype, "types", None), (list, tuple)) and getattr(ptype, "is_composite", False)


def _value_token(ptype: Any) -> str:
    choices = getattr(ptype, "choices", None)
    if choices:
        return "[" + "|".join(str(_plain(c)) for c in choices) + "]"
    return type_name(ptype).upper()


def _range(ptype: Any) -> str | None:
    if not hasattr(ptype, "min_open"):
        return None
    lo, hi = getattr(ptype, "min", None), getattr(ptype, "max", None)
    lo_op = "<" if ptype.min_open else "<="
    hi_op = "<" if ptype.max_open else "<="
    if lo is not None and hi is not None:
        return f"{lo}{lo_op}x{hi_op}{hi}"
    if lo is not None:
        return f"x{'>' if ptype.min_open else '>='}{lo}"
    if hi is not None:
        return f"x{hi_op}{hi}"
    return None


def _default(p: Any, is_flag: bool) -> str | None:
    value = p.default
    if value is None or callable(value) or type(value).__name__ == "Sentinel":
        return None
    if is_flag and value is False and not getattr(p, "secondary_opts", None):
        return None
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return ", ".join(str(_plain(v)) for v in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value == "":
        return None
    return str(_plain(value))


def _plain(value: Any) -> Any:
    return value.value if isinstance(value, enum.Enum) else value


def _short_help(cmd: Any) -> str | None:
    if getattr(cmd, "short_help", None):
        return _clean(cmd.short_help, strip_deprecated=True)
    getter = getattr(cmd, "get_short_help_str", None)
    if getter is None:
        return None
    try:
        text = getter(limit=200)
    except TypeError:  # pragma: no cover - very old Click
        text = getter()
    return _clean(text, strip_deprecated=True)


def _clean(text: str | None, *, strip_deprecated: bool = False) -> str | None:
    if not text:
        return None
    # Click's "\b" marks a paragraph that must not be rewrapped; drop it.
    lines = [line for line in inspect.cleandoc(text).splitlines() if line.strip() != "\b"]
    text = "\n".join(lines).strip()
    if strip_deprecated:
        text = _DEPRECATED_RE.sub(" ", text).strip()
    return text or None
