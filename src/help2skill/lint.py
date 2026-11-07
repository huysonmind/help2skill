"""Check the command lines in a project's documentation against the real CLI.

Unlike :func:`help2skill.check`, this needs no SKILL.md: point it at a README
and a ``docs/`` folder (Markdown, MDX or reStructuredText) and every example
that runs the CLI is checked for unknown subcommands, unknown or misplaced
options, invalid choices and missing arguments.
"""

from __future__ import annotations

import fnmatch
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ._snippets import snippets_for
from .model import Command
from .sync import Problem, check_snippets, without_block

DOC_SUFFIXES = (".md", ".mdx", ".markdown", ".rst", ".rest")
# Directories never searched for documentation.
SKIP_DIRS = frozenset(
    {
        ".git", ".hg", ".venv", "venv", ".tox", ".nox", "node_modules", "site-packages",
        "build", "dist", "_build", "site", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    }
)  # fmt: skip
# Changelogs and release notes (files or folders) describe old versions, so their
# commands are expected to differ.
_CHANGELOG_RE = re.compile(r"^(change(s|log)|history|news|release[-_ ]?notes)([-_.].*)?$", re.I)
DEFAULT_PATHS = ("README.md", "README.rst", "README.mdx", "docs", "doc")


@dataclass
class FileResult:
    """Problems found in one document, and how many of its lines run the CLI."""

    path: Path
    problems: list[Problem] = field(default_factory=list)
    checked: int = 0


def find_docs(paths: Iterable[str | Path], *, exclude: Iterable[str] = ()) -> list[Path]:
    """Documentation files under ``paths``, sorted.

    Directories are searched recursively for Markdown, MDX and reStructuredText
    files, skipping virtual environments, build output and changelogs. A file
    named explicitly is always included. ``exclude`` holds glob patterns matched
    against the file path and name.
    """
    patterns = list(exclude)
    found: set[Path] = set()
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            found.add(path)
            continue
        if not path.is_dir():
            raise FileNotFoundError(f"{path} not found")
        for root, dirs, files in os.walk(path):
            dirs[:] = sorted(
                d for d in dirs if d not in SKIP_DIRS and not d.startswith(".") and not _CHANGELOG_RE.match(d)
            )
            for name in files:
                if not name.lower().endswith(DOC_SUFFIXES) or _CHANGELOG_RE.match(name):
                    continue
                found.add(Path(root) / name)
    return sorted(p for p in found if not _excluded(p, patterns))


def default_paths(directory: str | Path = ".") -> list[Path]:
    """The README and ``docs/`` folder of a project, those that exist."""
    base = Path(directory)
    return [base / name for name in DEFAULT_PATHS if (base / name).exists()]


def _excluded(path: Path, patterns: list[str]) -> bool:
    text = path.as_posix()
    return any(
        fnmatch.fnmatch(text, pattern)
        or fnmatch.fnmatch(path.name, pattern)
        or text.startswith(pattern.rstrip("/") + "/")
        for pattern in patterns
    )


def lint_text(
    text: str, cmd: Command, *, filename: str = "doc.md", scripts: tuple[str, ...] = ()
) -> FileResult:
    """Check one document's text; ``filename`` picks the format (``.rst`` or Markdown)."""
    problems, checked = check_snippets(snippets_for(filename, without_block(text)), cmd, scripts=scripts)
    return FileResult(Path(filename), problems, checked)


def lint_files(
    cmd: Command, files: Iterable[str | Path], *, scripts: tuple[str, ...] = ()
) -> list[FileResult]:
    """Check every file; returns one result per file, in order."""
    results = []
    for file in files:
        path = Path(file)
        text = path.read_text(encoding="utf-8", errors="replace")
        result = lint_text(text, cmd, filename=path.name, scripts=scripts)
        result.path = path
        results.append(result)
    return results
