"""Compact output, split skills, launcher prefixes, home redaction, lazy commands."""

from __future__ import annotations

import os

import click
import pytest
from click.testing import CliRunner
from sample_clis import notes

import help2skill
from help2skill.click import add_llms_option
from help2skill.privacy import find_machine_paths, redact_home
from help2skill.sync import check_references


@pytest.fixture
def tree():
    return help2skill.introspect(notes, "notes")


# --- compact output -------------------------------------------------------------


def test_render_llms_falls_back_to_index(tree):
    full = help2skill.render_llms(tree, max_chars=0)
    assert full == help2skill.render_markdown(tree)
    short = help2skill.render_llms(tree, max_chars=100)
    assert short.startswith("# `notes [OPTIONS] COMMAND [ARGS]...`")
    assert "- `notes db migrate` (deprecated)" in short
    assert "## `notes add" not in short
    assert "run `notes <command> --llms`" in short


def test_leaf_command_is_never_shortened(tree):
    add = tree.get("add")
    assert help2skill.render_llms(add, max_chars=10) == help2skill.render_markdown(add)


def test_llms_env_budget(monkeypatch):
    monkeypatch.setenv("HELP2SKILL_LLMS_MAX_CHARS", "100")
    out = CliRunner().invoke(notes, ["--llms"], prog_name="notes").output
    assert "Index only" in out and "## `notes add" not in out
    monkeypatch.setenv("HELP2SKILL_LLMS_MAX_CHARS", "0")
    out = CliRunner().invoke(notes, ["--llms"], prog_name="notes").output
    assert "## `notes add" in out


def test_split_skill_round_trip(tmp_path):
    path = help2skill.write_skill(notes, tmp_path / "notes" / "SKILL.md", name="notes", max_chars=100)
    reference = path.parent / help2skill.REFERENCE_FILE
    assert reference.exists()
    assert "references/commands.md" in path.read_text()
    assert "## `notes add" in reference.read_text()
    assert help2skill.check_skill_file(notes, path, max_chars=100) == []

    reference.write_text(reference.read_text() + "\nedited by hand\n")
    kinds = [p.kind for p in help2skill.check_skill_file(notes, path, max_chars=100)]
    assert kinds == ["stale-reference"]
    reference.unlink()
    kinds = [p.kind for p in help2skill.check_skill_file(notes, path, max_chars=100)]
    assert kinds == ["missing-reference"]

    # Growing the budget back merges everything into SKILL.md and removes the file.
    help2skill.write_skill(notes, path, name="notes", max_chars=0)
    assert not reference.exists()
    assert help2skill.check_skill_file(notes, path, max_chars=0) == []


# --- launcher prefixes ------------------------------------------------------------


@pytest.mark.parametrize(
    "snippet",
    [
        "uv run notes add T --tag x",
        "uv run --with pillow notes add T",
        "uv run --python 3.12 notes db migrate",
        "CB_MODE=1 DEBUG=1 uv run notes add T",
        "uvx --from notes-pkg notes add T",
        "uv tool run notes add T",
        "poetry run notes add T",
        "pipx run notes add T",
        "python -m notes add T",
        "python3.12 -m notes db migrate --dry-run",
    ],
)
def test_launcher_prefixes_are_understood(tree, snippet):
    assert check_references(f"`{snippet}`", tree) == []
    assert [p.kind for p in check_references(f"`{snippet} --nope`", tree)] == ["unknown-option"]


@pytest.mark.parametrize("snippet", ["uv run other add --nope", "python -m other --nope", "uv sync --nope"])
def test_other_programs_are_ignored(tree, snippet):
    assert check_references(f"`{snippet}`", tree) == []


# --- home directory -----------------------------------------------------------------


def test_redact_home():
    text = "cache in /home/alice/.cache and /home/alice, not /home/alicex/x"
    assert redact_home(text, "/home/alice") == "cache in ~/.cache and ~, not /home/alicex/x"


def test_find_machine_paths():
    text = "a /Users/bob/x b /home/carol c C:\\Users\\dan\\x d ~/ok"
    assert find_machine_paths(text) == ["/Users/bob", "/home/carol", "C:\\Users\\dan"]


def test_skill_is_redacted_and_stable(tmp_path, monkeypatch):
    @click.command()
    @click.option("--cache", default=str(tmp_path / "home" / "me" / ".cache"), show_default=True)
    def tool(cache: str) -> None:
        """Tool."""

    home = str(tmp_path / "home" / "me")
    monkeypatch.setenv("HOME", home)
    monkeypatch.setenv("USERPROFILE", home)  # Path.home() on Windows
    path = help2skill.write_skill(tool, tmp_path / "SKILL.md", name="tool")
    assert f"(default: ~{os.sep}.cache)" in path.read_text()
    assert help2skill.check_skill_file(tool, path) == []


def test_cli_warns_about_foreign_home(tmp_path, capsys, monkeypatch):
    from help2skill.cli import main

    module = tmp_path / "foreign_cli.py"
    module.write_text(
        "import click\n"
        "@click.command()\n"
        "@click.option('--cache', default='/home/someone-else/.cache', show_default=True)\n"
        "def tool(cache):\n    'Tool.'\n"
    )
    monkeypatch.chdir(tmp_path)
    assert main(["markdown", "foreign_cli:tool", "--program", "tool"]) == 0
    assert "machine-specific path '/home/someone-else'" in capsys.readouterr().err


# --- lazy placeholder commands ----------------------------------------------------------


class Placeholder(click.Command):
    """Like Hugging Face's LazyHfCommand: params appear only after materialize()."""

    def __init__(self, name: str, real: click.Command) -> None:
        super().__init__(name=name)
        self._real = real

    def materialize(self) -> click.Command:
        return self._real


@click.command()
@click.option("--repo", required=True, help="Repository id.")
def _download(repo: str) -> None:
    """Download files."""


def _lazy_group() -> click.Group:
    group = click.Group("hub")
    group.add_command(Placeholder("download", _download))
    return group


def test_default_resolve_materializes():
    tree = help2skill.introspect(_lazy_group())
    download = tree.get("download")
    assert download.help == "Download files."
    assert [p.opts for p in download.options] == [["--repo"]]


def test_custom_resolve():
    calls = []

    def resolve(cmd):
        calls.append(cmd.name)
        return cmd

    tree = help2skill.introspect(_lazy_group(), resolve=resolve)
    assert "download" in calls
    assert tree.get("download").options == []


def test_llms_flag_materializes_lazy_commands():
    group = add_llms_option(_lazy_group())
    out = CliRunner().invoke(group, ["--llms"], prog_name="hub").output
    assert "- `--repo TEXT` (required): Repository id." in out
