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
        for sub in self.subcommands:
            if sub.name == name:
                return sub
        return None

    def find(self, path: list[str]) -> Command | None:
        """Resolve a list of subcommand names below this command."""
        node: Command | None = self
        for part in path:
            node = node.get(part) if node else None
        return node
