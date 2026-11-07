"""Framework-neutral description of a command-line interface."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class Param:
    """One option or positional argument."""

    name: str
    kind: str  # "option" or "argument"
    opts: list[str] = field(default_factory=list)
    secondary_opts: list[str] = field(default_factory=list)
    type: str = "text"
    choices: list[str] | None = None
    required: bool = False
    default: str | None = None
    is_flag: bool = False
    multiple: bool = False
    nargs: int | str = 1
    envvars: list[str] = field(default_factory=list)
    help: str | None = None
    metavar: str | None = None
    # One token per value slot, e.g. ["NAME", "[integer|text]"] for a 2-tuple option.
    value_tokens: list[str] | None = None
    count: bool = False  # -v, -vv, -vvv
    range: str | None = None  # e.g. "1<=x<=50"
    case_insensitive: bool = False
    prompts: bool = False  # asks interactively when omitted
    optional_value: bool = False  # option may be given without its value

    @property
    def is_option(self) -> bool:
        return self.kind == "option"


@dataclass
class Command:
    """A command or command group, with its full invocation path."""

    name: str
    path: list[str]
    help: str | None = None
    short_help: str | None = None
    params: list[Param] = field(default_factory=list)
    subcommands: list[Command] = field(default_factory=list)
    deprecated: bool = False
    # Subcommand run when the first token is not a subcommand name (click-default-group).
    default_command: str | None = None
    aliases: list[str] = field(default_factory=list)
    # Names that run a command but are not documented (hidden commands).
    hidden_subcommands: list[str] = field(default_factory=list)
    # Groups of options that cannot be combined: (option names, one is required).
    exclusive: list[tuple[list[str], bool]] = field(default_factory=list)
    # Unknown options are passed on as arguments (Click ``ignore_unknown_options``).
    passthrough: bool = False

    @property
    def is_group(self) -> bool:
        return bool(self.subcommands)

    @property
    def options(self) -> list[Param]:
        return [p for p in self.params if p.is_option]

    @property
    def arguments(self) -> list[Param]:
        return [p for p in self.params if not p.is_option]

    def walk(self) -> Iterator[Command]:
        """Yield this command and every descendant, depth first."""
        yield self
        for sub in self.subcommands:
            yield from sub.walk()

    def get(self, name: str) -> Command | None:
        """Find a direct subcommand by name or alias."""
        for sub in self.subcommands:
            if sub.name == name or name in sub.aliases:
                return sub
        return None

    def find(self, path: list[str]) -> Command | None:
        """Resolve a list of subcommand names below this command."""
        node: Command | None = self
        for part in path:
            node = node.get(part) if node else None
        return node
