"""The ``help2skill`` command."""

from __future__ import annotations

import argparse
import difflib
import importlib
import os
import shlex
import sys
from pathlib import Path
from typing import Any

from . import (
    REFERENCE_FILE,
    SKILL_MAX_CHARS,
    UNNAMED,
    __version__,
    check_skill_file,
    find_machine_paths,
    introspect,
    program_name,
    read_settings,
    redact_home,
    render_llms,
    write_skill,
)
from ._cyclopts import is_cyclopts_app
from ._plumbum import is_plumbum_app
from .sync import count_command_lines

_STALE_KINDS = ("stale-block", "missing-block", "stale-reference", "missing-reference")


class UsageError(Exception):
    """A problem with the user's input: printed as one line, exit status 2."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="help2skill",
        description=(
            "Generate LLM-ready docs and SKILL.md files from Click, Typer, argparse, cyclopts "
            "and plumbum CLIs."
        ),
        epilog="TARGET is the import path of the CLI object, e.g. mypkg.cli:app. For a function "
        "that builds an argparse parser, write mypkg.cli:build_parser() (with parentheses).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="action", required=True)

    md = sub.add_parser("markdown", help="Print the Markdown reference for a CLI.")
    md.add_argument("target", help="CLI object, e.g. mypkg.cli:app")
    md.add_argument(
        "--max-chars",
        type=int,
        default=0,
        help="Print only an index when the reference is longer than this (default: 0 = no limit)",
    )

    skill = sub.add_parser("skill", help="Create a SKILL.md, or refresh its generated block.")
    skill.add_argument("target", help="CLI object, e.g. mypkg.cli:app")
    skill.add_argument(
        "--name", help="Skill name: lowercase letters, digits, hyphens (needed to create the file)"
    )
    skill.add_argument("--description", help="Skill description (default: from the CLI help)")
    skill.add_argument(
        "--output",
        "-o",
        type=Path,
        help="SKILL.md path (default: skills/<name>/SKILL.md)",
    )
    skill.add_argument(
        "--max-chars",
        type=int,
        help=f"Above this size, keep an index in SKILL.md and the full reference in {REFERENCE_FILE} "
        f"(default: {SKILL_MAX_CHARS}, or the value stored in the file; 0 = never split)",
    )

    chk = sub.add_parser("check", help="Exit 1 if a SKILL.md has drifted from the CLI.")
    chk.add_argument("target", help="CLI object, e.g. mypkg.cli:app")
    chk.add_argument("path", type=Path, help="SKILL.md to check")
    chk.add_argument("--max-chars", type=int, help="Override the value stored in the file")
    for p in (md, skill, chk):
        p.add_argument(
            "--program",
            help="Program name users type (default: stored in the file, else the console script "
            "that points at TARGET, else the CLI's own name)",
        )
        p.add_argument(
            "--hide-default",
            action="append",
            metavar="NAME",
            dest="hide_defaults",
            help="Leave out the default of this parameter (name or option), e.g. one computed at "
            "run time; repeatable. Stored in the file.",
        )
        p.add_argument(
            "--app-dir",
            metavar="DIR",
            help="Import TARGET from this directory, e.g. src (default: the current directory)",
        )
        p.add_argument(
            "--resolve",
            metavar="MODULE:FUNC",
            help="Function that turns a lazy placeholder command into the real command",
        )
        p.add_argument(
            "--from-main",
            action="store_true",
            help="TARGET is a main() function that builds an argparse parser and parses sys.argv: "
            "run it until it parses, and use that parser. Code in main() before parsing runs.",
        )
    return parser


class _Captured(Exception):
    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser


def capture_parser(main: Any) -> argparse.ArgumentParser:
    """Run ``main()`` until it parses its arguments, and return that argparse parser.

    For scripts that build the parser inside ``main()``. Whatever ``main()`` does
    before parsing still runs; nothing after it does.
    """

    def stop(self: argparse.ArgumentParser, *args: Any, **kwargs: Any) -> Any:
        raise _Captured(self)

    names = ("parse_args", "parse_known_args")
    saved = {name: getattr(argparse.ArgumentParser, name) for name in names}
    for name in names:
        setattr(argparse.ArgumentParser, name, stop)
    try:
        main()
    except _Captured as captured:
        return captured.parser
    finally:
        for name, method in saved.items():
            setattr(argparse.ArgumentParser, name, method)
    raise UsageError(f"{getattr(main, '__name__', main)}() returned without parsing arguments with argparse")


def load_target(spec: str, *, call: bool = True, app_dir: str | None = None, from_main: bool = False) -> Any:
    """Import ``module:attr``; ``module:func()`` calls ``func`` (e.g. a parser factory).

    ``from_main`` runs ``attr`` (a ``main()`` function) until it parses its
    arguments and returns that parser, see :func:`capture_parser`.
    """
    module_name, _, attr = spec.partition(":")
    if not module_name or not attr or "/" in module_name or module_name.endswith(".py"):
        raise UsageError(f"target must look like module.path:attribute, got {spec!r}")
    explicit_call = attr.endswith("()")
    attr = attr.removesuffix("()")
    for directory in (os.getcwd(), app_dir):
        if directory and os.path.abspath(directory) not in sys.path:
            sys.path.insert(0, os.path.abspath(directory))
    # argparse names an unnamed parser after sys.argv[0]; make that detectable.
    saved_argv = sys.argv
    sys.argv = [UNNAMED, *sys.argv[1:]]
    try:
        try:
            obj: Any = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            raise UsageError(
                f"cannot import {module_name!r}: {exc}{_src_hint(module_name, app_dir)}"
            ) from exc
        for part in attr.split("."):
            if not hasattr(obj, part):
                names = [n for n in dir(obj) if not n.startswith("_")]
                close = difflib.get_close_matches(part, names, n=1)
                hint = f"; did you mean {close[0]!r}?" if close else ""
                raise UsageError(f"{module_name!r} has no attribute {attr!r}{hint}")
            obj = getattr(obj, part)
        if from_main:
            if not callable(obj):
                raise UsageError(f"--from-main: {spec} is not a function")
            obj = capture_parser(obj)
        elif call and explicit_call:
            obj = obj()
        elif call and callable(obj) and not _is_cli_object(obj):
            if "parser" not in attr.rsplit(".", 1)[-1].lower():
                raise UsageError(
                    f"{spec} is a function, not a CLI object (Click, Typer, argparse, cyclopts, plumbum). "
                    f"If it returns a parser, write {spec}() to call it; if it builds and parses one "
                    "inside, add --from-main."
                )
            obj = obj()
    except SystemExit as exc:
        raise UsageError(f"importing {spec} exited (status {exc.code}); point at the CLI object") from exc
    finally:
        sys.argv = saved_argv
    return obj


def _src_hint(module_name: str, app_dir: str | None) -> str:
    top = module_name.split(".")[0]
    if app_dir is None and (Path("src") / top).exists():
        return "; the package is under src/: add --app-dir src or install the project (pip install -e .)"
    return ""


def _is_cli_object(obj: Any) -> bool:
    return (
        isinstance(obj, argparse.ArgumentParser)
        or hasattr(obj, "registered_commands")
        or (hasattr(obj, "params") and hasattr(obj, "make_context"))
        or is_cyclopts_app(obj)
        or is_plumbum_app(obj)
    )


def entry_point_name(spec: str) -> str | None:
    """Name of the installed console script that runs ``spec`` (``module:attr``), if any."""
    from importlib.metadata import entry_points

    target = spec.removesuffix("()").replace(" ", "")
    for ep in entry_points(group="console_scripts"):
        if ep.value.replace(" ", "") == target:
            return ep.name
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except UsageError as exc:
        print(f"help2skill: error: {exc}", file=sys.stderr)
        return 2
    except (ValueError, TypeError, FileNotFoundError) as exc:
        print(f"help2skill: error: {exc}", file=sys.stderr)
        return 2


def _run(args: argparse.Namespace) -> int:
    cli = load_target(args.target, app_dir=args.app_dir, from_main=args.from_main)
    resolve = load_target(args.resolve, call=False, app_dir=args.app_dir) if args.resolve else None
    stored = None
    if args.action == "skill" and args.output and args.output.exists():
        stored = read_settings(args.output.read_text(encoding="utf-8")).program
    if args.action == "check" and args.path.exists():
        stored = read_settings(args.path.read_text(encoding="utf-8")).program
    program = program_name(cli, args.program, stored, entry_point_name(args.target), resolve=resolve)

    if args.action == "markdown":
        if program is None:
            _warn_unnamed(introspect(cli, resolve=resolve).name)
        cmd = introspect(cli, program, resolve=resolve, hide_defaults=args.hide_defaults)
        text = redact_home(render_llms(cmd, max_chars=args.max_chars))
        _warn_machine_paths(text, "output")
        sys.stdout.write(text)
        return 0

    if args.action == "skill":
        if args.output is None and not args.name:
            raise UsageError("pass --name (to create skills/<name>/SKILL.md) or --output PATH")
        output = args.output or Path("skills") / args.name / "SKILL.md"
        path = write_skill(
            cli,
            output,
            name=args.name,
            description=args.description,
            program=program,
            max_chars=args.max_chars,
            resolve=resolve,
            hide_defaults=args.hide_defaults,
        )
        print(f"wrote {path}")
        reference = path.parent / REFERENCE_FILE
        if reference.exists():
            print(f"wrote {reference}")
        for written in (path, reference):
            if written.exists():
                _warn_machine_paths(written.read_text(encoding="utf-8"), str(written))
        return 0

    problems = check_skill_file(
        cli,
        args.path,
        program=program,
        max_chars=args.max_chars,
        resolve=resolve,
        hide_defaults=args.hide_defaults,
        scripts=_script_names(args.target),
    )
    for problem in problems:
        print(f"{args.path}: {problem}", file=sys.stderr)
    if any(p.kind in _STALE_KINDS for p in problems):
        print(f"help2skill: regenerate with: {_regenerate_command(args)}", file=sys.stderr)
    if problems:
        return 1
    text = args.path.read_text(encoding="utf-8")
    prog = program or read_settings(text).program or introspect(cli, resolve=resolve).name
    checked = count_command_lines(text, prog, scripts=_script_names(args.target))
    if checked:
        lines = f"{checked} hand-written command line{'s' if checked != 1 else ''} checked"
    else:
        lines = f"no hand-written `{prog}` command lines found to check"
    print(f"{args.path}: in sync with {args.target} ({lines})")
    return 0


def _warn_unnamed(name: str) -> None:
    shown = "the script name" if name == UNNAMED else repr(name)
    print(
        f"help2skill: warning: program name unknown (the CLI calls itself {shown}); "
        "pass --program NAME or install the console script",
        file=sys.stderr,
    )


def _warn_machine_paths(text: str, where: str) -> None:
    for found in find_machine_paths(text):
        print(
            f"help2skill: warning: {where} contains a machine-specific path {found!r}; "
            "review it before committing",
            file=sys.stderr,
        )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


def _regenerate_command(args: argparse.Namespace) -> str:
    """The ``help2skill skill`` command that refreshes the checked file, ready to paste."""
    parts = ["help2skill", "skill", args.target, "-o", str(args.path)]
    if args.app_dir:
        parts += ["--app-dir", str(args.app_dir)]
    if args.resolve:
        parts += ["--resolve", args.resolve]
    if args.from_main:
        parts.append("--from-main")
    return shlex.join(parts)


def _script_names(spec: str) -> tuple[str, ...]:
    """File name of the target module, so ``python path/to/tool.py …`` lines are checked."""
    module = sys.modules.get(spec.partition(":")[0])
    file = getattr(module, "__file__", None)
    if not file:
        return ()
    name = Path(file).name
    return () if name == "__init__.py" else (name,)
