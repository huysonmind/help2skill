"""Find command lines in Markdown and reStructuredText documents.

Each snippet is ``(line number, text, in_block)``: ``in_block`` is true for a
line of a shell code block (a whole command line) and false for an inline code
span in prose, which often names a command without its arguments.

Code blocks in other languages (Python, TOML, JSON…) are skipped. In console
blocks (``console``, ``shell-session``) that use a prompt (``$ ``), only the
prompt lines are commands; the others are output. A line, or the line just before a code block,
containing ``help2skill: ignore`` is skipped. Untagged blocks drawn with
box-drawing characters (diagrams) are skipped too. Mermaid diagrams are read
for the commands in their labels.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

Snippet = tuple[int, str, bool]

IGNORE_MARKER = "help2skill: ignore"

# Code block languages whose lines are commands.
SHELL_LANGS = frozenset(
    {
        "", "bash", "sh", "shell", "zsh", "fish", "ksh", "text", "txt", "plain", "plaintext",
        "none", "cmd", "bat", "batch", "powershell", "ps1", "pwsh",
    }
)  # fmt: skip
# Languages that mix commands (after a prompt) with their output.
PROMPT_LANGS = frozenset(
    {"console", "shell-session", "shellsession", "sh-session", "bash-session", "terminal", "doscon"}
)
# Untagged or plain-text blocks holding these are diagrams, not commands.
_PLAIN_LANGS = frozenset({"", "text", "txt", "plain", "plaintext", "none"})
_DIAGRAM_RE = re.compile("[\u2500-\u25ff]")
_PROMPT_RE = re.compile(r"^\s*(?:\(\S+\)\s*)?(?:\$|%|>|PS>|PS [^>]*>)\s")

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*\{?\.?([\w+-]*)")
_CODE_SPAN_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")

_RST_DIRECTIVE_RE = re.compile(r"^(\s*)\.\.\s+(code-block|code|sourcecode|prompt)::\s*(\S*)")
_RST_INLINE_RE = re.compile(r"``([^`\n]+)``")
_RST_OPTION_RE = re.compile(r"^\s*:[\w-]+:(\s|$)")


def markdown_snippets(text: str) -> Iterator[Snippet]:
    """Command lines in Markdown (also MDX): fenced code blocks and code spans."""
    lines = text.splitlines()
    previous = ""  # last non-blank line before the current one
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            block = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(marker):
                block.append((j + 1, lines[j]))
                j += 1
            if IGNORE_MARKER not in line and IGNORE_MARKER not in previous:
                lang = fence.group(2).lower()
                if lang == "mermaid":
                    yield from mermaid_snippets(block)
                else:
                    yield from block_snippets(block, lang)
            previous = ""
            i = j + 1
            continue
        if IGNORE_MARKER not in line:
            yield from _line_spans(i + 1, line)
        if line.strip():
            previous = line
        i += 1


def _line_spans(lineno: int, line: str) -> Iterator[Snippet]:
    """Code spans of one line of prose.

    In a table row whose first cell is one command (`` `tool sub` ``, not
    ``tool a / b``) and
    whose other cells hold only options (`` `--json` ``), the options belong to
    that command, so they are checked with it.
    """
    spans = [m.group(1) for m in _CODE_SPAN_RE.finditer(line)]
    if line.lstrip().startswith("|"):
        first, _, rest = line.strip().strip("|").partition("|")
        command = re.fullmatch(r"\s*`([^`]+)`\s*", first)
        others = [m.group(1) for m in _CODE_SPAN_RE.finditer(rest)]
        single = command is not None and not re.search(r"/|,|\bor\b|\|", command.group(1))
        if command is not None and single and others and all(span.startswith("--") for span in others):
            yield lineno, " ".join([command.group(1), *others]), False
            return
    for span in spans:
        yield lineno, span, False


# Mermaid labels and arrows: what is left between them is plain text.
_MERMAID_SEP_RE = re.compile(r"<br\s*/?>|-+\.?-+>|=+>|-{3,}|[\[\]{}()|<>\"]+")


def mermaid_snippets(lines: Iterable[tuple[int, str]]) -> Iterator[Snippet]:
    """Command lines in the node and edge labels of a Mermaid diagram."""
    for lineno, line in lines:
        if IGNORE_MARKER in line or line.lstrip().startswith("%%"):
            continue  # %% starts a Mermaid comment
        for fragment in _MERMAID_SEP_RE.split(line):
            fragment = fragment.strip()
            if fragment:
                yield lineno, fragment, False


def rst_snippets(text: str) -> Iterator[Snippet]:
    """Command lines in reStructuredText: code blocks, ``::`` literal blocks, inline literals.

    A ``::`` literal block has no language, so only its prompt lines (``$ cmd``)
    are taken as commands.
    """
    lines = text.splitlines()
    previous = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        ignored = IGNORE_MARKER in line or IGNORE_MARKER in previous
        if IGNORE_MARKER not in line:
            for match in _RST_INLINE_RE.finditer(line):
                yield i + 1, match.group(1), False
        directive = _RST_DIRECTIVE_RE.match(line)
        stripped = line.strip()
        literal = not directive and stripped.endswith("::") and not stripped.startswith("..")
        if directive or literal:
            indent = len(line) - len(line.lstrip())
            block = []
            j = i + 1
            while j < len(lines):
                body = lines[j]
                if body.strip() and len(body) - len(body.lstrip()) <= indent:
                    break
                if not (directive and _RST_OPTION_RE.match(body)):
                    block.append((j + 1, body))
                j += 1
            if directive:
                kind, lang = directive.group(2), directive.group(3).lower()
                lang = "bash" if kind == "prompt" else lang
            else:
                lang = "console"
            if not ignored:
                yield from block_snippets(block, lang)
            previous = ""
            i = j
            continue
        if stripped:
            previous = line
        i += 1


def block_snippets(lines: Iterable[tuple[int, str]], lang: str) -> Iterator[Snippet]:
    """Command lines of one code block, joining lines continued with a backslash."""
    lang = lang.lower()
    if lang not in PROMPT_LANGS and lang not in SHELL_LANGS:
        return
    lines = list(lines)
    if lang in _PLAIN_LANGS and any(_DIAGRAM_RE.search(line) for _, line in lines):
        return  # box-drawing characters: an ASCII diagram
    # A console block without any prompt holds only commands.
    prompt_only = lang in PROMPT_LANGS and any(_PROMPT_RE.match(line) for _, line in lines)
    pending: tuple[int, str] | None = None
    for lineno, line in lines:
        if pending:
            lineno, line = pending[0], pending[1] + " " + line.strip()
            pending = None
        elif prompt_only:
            prompt = _PROMPT_RE.match(line)
            if not prompt:
                continue
            line = line[prompt.end() :]
        if line.rstrip().endswith("\\"):
            pending = (lineno, line.rstrip()[:-1])
            continue
        if IGNORE_MARKER not in line:
            yield lineno, line, True
    if pending:
        yield (*pending, True)


def snippets_for(path_name: str, text: str) -> Iterator[Snippet]:
    """Snippets of a document, parsed by its file extension."""
    if path_name.lower().endswith((".rst", ".rest")):
        return rst_snippets(text)
    return markdown_snippets(text)
