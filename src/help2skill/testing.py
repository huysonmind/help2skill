"""pytest helper: fail the build when SKILL.md drifts from the CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import check_skill_file
from ._click import Resolver


def assert_skill_in_sync(
    cli: Any,
    path: str | Path,
    *,
    program: str | None = None,
    max_chars: int | None = None,
    resolve: Resolver | None = None,
    hide_defaults: list[str] | None = None,
) -> None:
    """Raise ``AssertionError`` listing every drift problem.

    Settings not passed are read from the file (``help2skill skill`` stores them).
    Build ``path`` from ``__file__`` so the test passes from any directory.
    """
    problems = check_skill_file(
        cli, path, program=program, max_chars=max_chars, resolve=resolve, hide_defaults=hide_defaults
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
