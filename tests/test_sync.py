from __future__ import annotations

import pytest
from sample_clis import build_parser, notes, typer_app

import help2skill
from help2skill.sync import check_references, extract_block
from help2skill.testing import assert_skill_in_sync

HAND_WRITTEN = """\
# Notes

Prefer `notes add "Buy milk" --tag home` for quick notes.
"""


@pytest.fixture
def tree():
    return help2skill.introspect(notes, "notes")


def test_update_block_keeps_hand_written_text(tree):
    text = help2skill.update_block(HAND_WRITTEN, "old\n")
    text = help2skill.update_block(text, help2skill.render_markdown(tree, level=2))
    assert text.startswith(HAND_WRITTEN)
    assert text.count("help2skill:begin") == 1
    assert "old" not in extract_block(text)


def test_fresh_skill_is_in_sync(tmp_path):
    path = help2skill.write_skill(notes, tmp_path / "notes" / "SKILL.md", name="notes")
    assert help2skill.check_skill_file(notes, path) == []
    assert_skill_in_sync(notes, path)


def test_rewrite_preserves_hand_written_body(tmp_path):
    path = help2skill.write_skill(notes, tmp_path / "SKILL.md", name="notes")
    path.write_text(path.read_text().replace("---\n\n", "---\n\n" + HAND_WRITTEN + "\n", 1))
    path.write_text(path.read_text().replace("Manage notes.", "Old text."))
    assert any(p.kind == "stale-block" for p in help2skill.check_skill_file(notes, path))
    help2skill.write_skill(notes, path, name="notes")
    assert HAND_WRITTEN in path.read_text()
    assert help2skill.check_skill_file(notes, path) == []


def test_missing_block(tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text("---\nname: notes\ndescription: x\n---\n" + HAND_WRITTEN)
    kinds = [p.kind for p in help2skill.check_skill_file(notes, path)]
    assert kinds == ["missing-block"]
    with pytest.raises(AssertionError, match="missing-block"):
        assert_skill_in_sync(notes, path)


@pytest.mark.parametrize(
    ("snippet", "expected"),
    [
        ("`notes add T --tag x`", []),
        ("`notes -v add T`", []),
        ("`notes add T --priority=high --llms`", []),
        ("`notes db migrate --dry-run`", []),
        ("`notes db COMMAND`", []),
        ("`notes <command> --help`", []),
        ("`notes add T | grep x --nope`", []),
        ("`other-tool --nope`", []),
        ("`notes remove T`", ["unknown-command"]),
        ("`notes db rollback`", ["unknown-command"]),
        ("`notes add T --color red`", ["unknown-option"]),
        ("`notes add T --verbose`", ["wrong-level-option"]),
    ],
)
def test_reference_checks(tree, snippet, expected):
    assert [p.kind for p in check_references(snippet, tree)] == expected


def test_reference_checks_in_fenced_blocks_report_line(tree):
    text = "intro\n```bash\n$ notes add T\n$ notes purge\n```\n`notes purge` again\n"
    problems = check_references(text, tree)
    assert [(p.kind, p.line) for p in problems] == [("unknown-command", 4), ("unknown-command", 6)]


def test_option_value_is_not_mistaken_for_a_command(tree):
    assert check_references("`notes add --priority high T`", tree) == []


def test_drift_detected_across_frameworks(tmp_path):
    # A skill generated from the Click CLI still matches the Typer and argparse twins
    # on every command and option name referenced by hand.
    skill = tmp_path / "SKILL.md"
    skill.write_text(HAND_WRITTEN + "\nRun `notes db migrate --dry-run` first.\n")
    for cli in (notes, typer_app, build_parser()):
        tree = help2skill.introspect(cli, "notes")
        assert check_references(skill.read_text(), tree) == []


def test_default_command_group():
    tree = help2skill.introspect(notes, "notes")
    tree.default_command = "add"
    assert check_references("`notes groceries --tag home`", tree) == []
    assert [p.kind for p in check_references("`notes groceries --nope`", tree)] == ["unknown-option"]


def test_default_command_takes_options_before_arguments():
    # click-default-group passes options the group does not know to the default command.
    tree = help2skill.introspect(notes, "notes")
    tree.default_command = "add"
    assert check_references("`notes --tag home groceries`", tree) == []
    problems = check_references("`notes --nope groceries`", tree)
    assert [p.kind for p in problems] == ["unknown-option"]


def test_prose_option_names_and_placeholders_are_skipped():
    tree = help2skill.introspect(notes, "notes")
    assert check_references("Use `notes add -t/--tag` to tag a note.", tree) == []
    assert check_references("`notes my_command --x`", tree) == []
    assert check_references("`notes your-plugin`", tree) == []
