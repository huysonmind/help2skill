"""Keep machine-specific paths out of generated files.

Help text is sometimes computed at runtime (``default: /Users/alice/.cache/...``).
Written files replace the current user's home directory with ``~``, which also keeps
the drift check stable between a laptop and CI.
"""

from __future__ import annotations

import os
import re
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


def find_machine_paths(text: str) -> list[str]:
    """Return home-directory-like paths left in ``text``, e.g. another user's."""
    return sorted(set(_MACHINE_PATH_RE.findall(text)))
