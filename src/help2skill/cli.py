"""The ``help2skill`` command."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import Any

from . import __version__, check_skill_file, introspect, render_markdown, write_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="help2skill",
        description="Generate LLM-ready docs and SKILL.md files from Click, Typer and argparse CLIs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="action", required=True)

    md = sub.add_parser("markdown", help="Print the Markdown reference for a CLI.")
    md.add_argument("target", help="Import path of the CLI object, e.g. mypkg.cli:app")
    md.add_argument("--program", help="Program name users type (default: from the CLI object)")

    skill = sub.add_parser("skill", help="Create a SKILL.md, or refresh its generated block.")
    skill.add_argument("target", help="Import path of the CLI object, e.g. mypkg.cli:app")
    skill.add_argument("--name", required=True, help="Skill name (lowercase letters, digits, hyphens)")
    skill.add_argument("--description", help="Skill description (default: from the CLI help)")
    skill.add_argument("--program", help="Program name users type (default: the skill name)")
    skill.add_argument(
        "--output",
        "-o",
        type=Path,
        help="SKILL.md path (default: skills/<name>/SKILL.md)",
    )

    chk = sub.add_parser("check", help="Exit 1 if a SKILL.md has drifted from the CLI.")
    chk.add_argument("target", help="Import path of the CLI object, e.g. mypkg.cli:app")
    chk.add_argument("path", type=Path, help="SKILL.md to check")
    chk.add_argument("--program", help="Program name users type (default: the skill name)")
    return parser


def load_target(spec: str) -> Any:
    """Import ``module:attr`` (attr may be dotted, or a function returning a parser)."""
    module_name, _, attr = spec.partition(":")
    if not module_name or not attr:
        raise SystemExit(f"help2skill: target must look like module:attr, got {spec!r}")
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    obj: Any = importlib.import_module(module_name)
    for part in attr.split("."):
        obj = getattr(obj, part)
    if callable(obj) and not _is_cli_object(obj):
        obj = obj()
    return obj


def _is_cli_object(obj: Any) -> bool:
    return (
        isinstance(obj, argparse.ArgumentParser)
        or hasattr(obj, "registered_commands")
        or (hasattr(obj, "params") and hasattr(obj, "make_context"))
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cli = load_target(args.target)
    if args.action == "markdown":
        sys.stdout.write(render_markdown(introspect(cli, args.program)))
        return 0
    if args.action == "skill":
        output = args.output or Path("skills") / args.name / "SKILL.md"
        path = write_skill(cli, output, name=args.name, description=args.description, program=args.program)
        print(f"wrote {path}")
        return 0
    problems = check_skill_file(cli, args.path, program=args.program)
    for problem in problems:
        print(f"{args.path}: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
