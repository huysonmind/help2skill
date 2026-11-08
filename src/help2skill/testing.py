"""pytest helpers: fail the build when SKILL.md or the docs drift from the CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import check_docs, check_skill_file
from ._click import Resolver


def assert_skill_in_sync(
    cli: Any,
    path: str | Path,
    *,
    program: str | None = None,
    max_chars: int | None = None,
    resolve: Resolver | None = None,
    hide_defaults: list[str] | None = None,
    scripts: tuple[str, ...] = (),
) -> None:
    """Raise ``AssertionError`` listing every drift problem.

    Settings not passed are read from the file (``help2skill skill`` stores them).
    Build ``path`` from ``__file__`` so the test passes from any directory.
    """
    problems = check_skill_file(
        cli,
        path,
        program=program,
        max_chars=max_chars,
        resolve=resolve,
        hide_defaults=hide_defaults,
        scripts=scripts,
    )
    if problems:
        details = "\n".join(f"- {p}" for p in problems)
        hint = ""
        if any(
            p.kind in ("stale-block", "missing-block", "stale-reference", "missing-reference")
            for p in problems
        ):
            hint = f"\nRegenerate the block with: help2skill skill MODULE:ATTR -o {path}"
        raise AssertionError(f"{path} is out of sync with the CLI:\n{details}{hint}")


def assert_docs_in_sync(
    cli: Any,
    paths: list[str | Path],
    *,
    program: str | None = None,
    resolve: Resolver | None = None,
    exclude: list[str] | tuple[str, ...] = (),
    scripts: tuple[str, ...] = (),
    global_options: bool = False,
) -> None:
    """Raise ``AssertionError`` listing every command line in ``paths`` the CLI would reject.

    ``paths`` are documentation files or directories (README.md, docs/); build
    them from ``__file__`` so the test passes from any directory.
    """
    results = check_docs(
        cli,
        paths,
        program=program,
        resolve=resolve,
        exclude=exclude,
        scripts=scripts,
        global_options=global_options,
    )
    lines = [f"- {r.path}:{p.line}: {p.message} [{p.kind}]" for r in results for p in r.problems]
    if lines:
        raise AssertionError("documentation is out of sync with the CLI:\n" + "\n".join(lines))
