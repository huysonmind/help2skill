"""Keep machine-specific paths out of generated files.

Help text is sometimes computed at runtime (``default: /Users/alice/.cache/...``).
Written files replace the current user's home directory with ``~``, which also keeps
the drift check stable between a laptop and CI.
"""

from __future__ import annotations

import getpass
import os
import re
import sys
import tempfile
from pathlib import Path

_MACHINE_PATH_RE = re.compile(r"(/Users/[^/\s`'\"]+|/home/[^/\s`'\"]+|[A-Za-z]:\\Users\\[^\\\s`'\"]+)")


def _home_variants(home: str | None) -> list[str]:
    home = home or str(Path.home())
    variants = {home, os.path.realpath(home)}
    return sorted((v.rstrip("/\\") for v in variants if len(v) > 1), key=len, reverse=True)


def redact_home(text: str, home: str | None = None) -> str:
    """Replace the home directory (``home`` or the current user's) with ``~``."""
    for variant in _home_variants(home):
        # Not followed by a name character, so /home/alice does not match /home/alicex.
        text = re.sub(re.escape(variant) + r"(?![\w-])", "~", text)
    return text


_ABS_PATH_RE = re.compile(r"(?<![\w.~])(?:/|[A-Za-z]:\\)[^\s`'\"<>|]+")


def _machine_prefixes() -> list[str]:
    """Locations that only exist on this machine: the environment and temp dirs."""
    found = set()
    for path in (sys.prefix, tempfile.gettempdir()):
        for variant in (path, os.path.realpath(path)):
            variant = variant.rstrip("/\\")
            if variant.count(os.sep) >= 2:  # skip "/" and "/tmp"-like roots
                found.add(variant)
    return sorted(found, key=len, reverse=True)


def _user_name() -> str | None:
    try:
        name = getpass.getuser()
    except Exception:  # pragma: no cover - no user database (some containers)
        return None
    return name if len(name) >= 3 else None


def find_machine_paths(text: str) -> list[str]:
    """Return machine-specific paths left in ``text``.

    Home-directory-like paths (another user's), paths inside the running
    environment or the temp directory, and paths containing the user name.
    """
    found = set(_MACHINE_PATH_RE.findall(text))
    prefixes = _machine_prefixes()
    user = _user_name()
    user_re = re.compile(rf"(?<![A-Za-z0-9]){re.escape(user)}(?![A-Za-z0-9])") if user else None
    for path in _ABS_PATH_RE.findall(text):
        path = path.rstrip(".,;:)")
        if any(path == p or path.startswith(p + os.sep) for p in prefixes) or (
            user_re and user_re.search(path)
        ):
            found.add(path)
    return sorted(found)
