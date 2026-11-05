"""Keep a hand-edited SKILL.md in sync with the real CLI.

Two kinds of drift are detected:

* the generated reference block (between markers) is stale;
* hand-written text outside the block mentions a subcommand or option the CLI
  does not have, or uses an option at the wrong level.
"""

from __future__ import annotations

import difflib
import re
import shlex
from dataclasses import dataclass

from .model import Command
from .render import render_markdown

BEGIN = "<!-- help2skill:begin (generated from the CLI; edit outside this block) -->"
END = "<!-- help2skill:end -->"
_BLOCK_RE = re.compile(r"<!-- help2skill:begin[^\n]*?-->\n?(.*?)<!-- help2skill:end -->", re.S)
_CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
_FENCE_RE = re.compile(r"^(```|~~~)")
_ALWAYS_OK = {"--help", "-h", "--llms"}
_STOP_TOKENS = {"|", "||", "&&", ";", ">", ">>", "<", "--"}


@dataclass
class Problem:
    kind: str  # missing-block | stale-block | unknown-command | wrong-level-option | unknown-option
    message: str
    line: int | None = None

    def __str__(self) -> str:
        where = f"line {self.line}: " if self.line else ""
        return f"{where}{self.message} [{self.kind}]"


def wrap_block(generated: str) -> str:
    return f"{BEGIN}\n{generated.rstrip()}\n{END}\n"


def extract_block(text: str) -> str | None:
    match = _BLOCK_RE.search(text)
    return match.group(1) if match else None


def update_block(text: str, generated: str) -> str:
    """Replace the generated block in ``text``, or append one if missing."""
    block = wrap_block(generated)
    if _BLOCK_RE.search(text):
        return _BLOCK_RE.sub(lambda _: block.rstrip("\n"), text, count=1)
    return text.rstrip("\n") + "\n\n" + block


def check(text: str, cmd: Command, *, level: int = 2) -> list[Problem]:
    """Return every drift problem between ``text`` (a SKILL.md) and ``cmd``."""
    problems: list[Problem] = []
    current = extract_block(text)
    expected = render_markdown(cmd, level=level)
    if current is None:
        problems.append(Problem("missing-block", "no help2skill generated block found"))
    elif current.strip() != expected.strip():
        diff = "\n".join(
            difflib.unified_diff(
                current.strip().splitlines(),
                expected.strip().splitlines(),
                "SKILL.md",
                "CLI",
                lineterm="",
            )
        )
        problems.append(Problem("stale-block", "generated block is out of date:\n" + diff))
    problems.extend(check_references(_without_block(text), cmd))
    return problems


def check_references(text: str, cmd: Command) -> list[Problem]:
    """Check command lines in code spans and fenced blocks of hand-written text."""
    problems = []
    for lineno, snippet in _snippets(text):
        problems.extend(_check_invocation(snippet, cmd, lineno))
    return problems


def _without_block(text: str) -> str:
    # Keep line numbers stable by blanking the block instead of removing it.
    return _BLOCK_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def _snippets(text: str):
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            yield lineno, line
        else:
            for match in _CODE_SPAN_RE.finditer(line):
                yield lineno, match.group(1)


def _check_invocation(snippet: str, root: Command, lineno: int) -> list[Problem]:
    snippet = snippet.strip().removeprefix("$ ")
    try:
        tokens = shlex.split(snippet, comments=True)
    except ValueError:
        return []
    if not tokens or tokens[0] != root.name:
        return []
    problems = []
    node = root
    ancestors = [root]
    expecting_value = False
    for token in tokens[1:]:
        if token in _STOP_TOKENS:
            break
        if expecting_value:
            expecting_value = False
            continue
        if token.startswith("-") and token != "-":
            flag = token.split("=", 1)[0]
            if flag in _ALWAYS_OK:
                continue
            param = _find_option(node, flag)
            if param is not None:
                expecting_value = not param.is_flag and "=" not in token
                continue
            owner = next((a for a in ancestors if _find_option(a, flag)), None)
            if owner is not None:
                problems.append(
                    Problem(
                        "wrong-level-option",
                        f"`{flag}` belongs to `{' '.join(owner.path)}`, "
                        f"not `{' '.join(node.path)}` (place it before the subcommand)",
                        lineno,
                    )
                )
            elif not _looks_like_short_cluster(flag):
                problems.append(
                    Problem("unknown-option", f"`{' '.join(node.path)}` has no option `{flag}`", lineno)
                )
            continue
        if node.is_group:
            child = node.get(token)
            if child is not None:
                node = child
                ancestors.append(child)
                continue
            default = node.get(node.default_command) if node.default_command else None
            if default is not None:
                # The token is the first argument of the default subcommand.
                node = default
                ancestors.append(node)
                continue
            if _is_placeholder(token):
                break
            problems.append(
                Problem("unknown-command", f"`{' '.join(node.path)}` has no subcommand `{token}`", lineno)
            )
            break
        # Leaf command: remaining positional tokens are argument values.
    return problems


def _find_option(cmd: Command, flag: str):
    for p in cmd.options:
        if flag in p.opts or flag in p.secondary_opts:
            return p
    return None


def _looks_like_short_cluster(flag: str) -> bool:
    # "-vvv" or "-n5": too ambiguous to judge without parser rules.
    return not flag.startswith("--") and len(flag) > 2


def _is_placeholder(token: str) -> bool:
    return token.isupper() or token.startswith(("<", "{", "[", "$")) or token in {"...", "…"}
