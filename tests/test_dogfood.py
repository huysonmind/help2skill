"""help2skill documents itself with its own SKILL.md."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from help2skill.cli import build_parser, main
from help2skill.testing import assert_skill_in_sync

SKILL = Path(__file__).parents[1] / "src/help2skill/.agents/skills/help2skill/SKILL.md"
TARGET = "help2skill.cli:build_parser()"


def test_own_skill_in_sync() -> None:
    assert_skill_in_sync(build_parser(), SKILL)


def test_shared_options_order_does_not_depend_on_hash_seed() -> None:
    code = (
        "import help2skill, help2skill.cli as c; "
        "print(help2skill.render_markdown(help2skill.introspect(c.build_parser())))"
    )
    outputs = set()
    for seed in ("0", "1", "2", "3"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
        )
        outputs.add(result.stdout)
    assert len(outputs) == 1
    assert "Shared options" in outputs.pop()


def test_regenerate_hint_is_shell_quoted(tmp_path: Path, capsys) -> None:
    stale = tmp_path / "SKILL.md"
    stale.write_text(SKILL.read_text().replace("Print the Markdown reference", "Old text", 1))
    assert main(["check", TARGET, str(stale), "--app-dir", "src"]) == 1
    err = capsys.readouterr().err
    assert f"help2skill skill '{TARGET}' -o {stale} --app-dir src" in err


def test_find_machine_paths_flags_environment_temp_and_user_paths(monkeypatch) -> None:
    import sys
    import tempfile

    from help2skill import privacy

    monkeypatch.setattr(privacy, "_user_name", lambda: "alice")
    venv_python = f"{sys.prefix}/bin/python"
    temp_file = f"{tempfile.gettempdir()}/build-1/out.txt"
    text = (
        f"default: {venv_python}. Cache in {temp_file}, logs in /var/folders/x/-Users-alice-proj/log; "
        "manuals in /usr/local/share/man, not /srv/malice/x"
    )
    found = privacy.find_machine_paths(text)
    assert venv_python in found
    assert temp_file in found
    assert "/var/folders/x/-Users-alice-proj/log" in found
    assert not any(p.startswith(("/usr/local", "/srv")) for p in found)


def test_todo_example_in_sync(monkeypatch) -> None:
    import pytest

    pytest.importorskip("typer")
    example = Path(__file__).parents[1] / "examples/todo"
    monkeypatch.syspath_prepend(str(example))
    import todo

    assert_skill_in_sync(todo.main, example / "SKILL.md")
