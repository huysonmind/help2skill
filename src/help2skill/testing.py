"""pytest helper: fail the build when SKILL.md drifts from the CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import check_skill_file


def assert_skill_in_sync(cli: Any, path: str | Path, *, program: str | None = None) -> None:
    """Raise ``AssertionError`` listing every drift problem.

    Fix a stale generated block with ``help2skill skill <module:attr> --output <path>``.
    """
    problems = check_skill_file(cli, path, program=program)
    if problems:
        details = "\n".join(f"- {p}" for p in problems)
        raise AssertionError(f"{path} is out of sync with the CLI:\n{details}")
