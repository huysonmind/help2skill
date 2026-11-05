from __future__ import annotations

from pathlib import Path

import pytest

from help2skill.cli import load_target, main

TESTS = Path(__file__).parent


@pytest.fixture(autouse=True)
def _cwd(monkeypatch):
    monkeypatch.chdir(TESTS)


@pytest.mark.parametrize("target", ["sample_clis:notes", "sample_clis:typer_app", "sample_clis:build_parser"])
def test_markdown(target, capsys):
    assert main(["markdown", target, "--program", "notes"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# `notes [OPTIONS] COMMAND [ARGS]...`")


def test_skill_then_check(tmp_path, capsys):
    path = tmp_path / "skills" / "notes" / "SKILL.md"
    assert main(["skill", "sample_clis:notes", "--name", "notes", "-o", str(path)]) == 0
    assert path.read_text().startswith("---\nname: notes\n")
    assert main(["check", "sample_clis:notes", str(path)]) == 0

    path.write_text(path.read_text() + "\nThen run `notes purge`.\n")
    assert main(["check", "sample_clis:notes", str(path)]) == 1
    assert "has no subcommand `purge`" in capsys.readouterr().err


def test_load_target_errors():
    with pytest.raises(SystemExit):
        load_target("no_colon")
    assert load_target("sample_clis:build_parser").prog == "notes"
