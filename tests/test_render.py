from __future__ import annotations

import pytest
from sample_clis import notes

import help2skill
from help2skill.render import validate_skill_metadata


@pytest.fixture
def tree():
    return help2skill.introspect(notes, "notes")


def test_markdown_reference(tree):
    md = help2skill.render_markdown(tree)
    assert md.startswith("# `notes [OPTIONS] COMMAND [ARGS]...`\n\nManage notes.")
    assert "- `-v, --verbose`: Show more output." in md
    assert "Commands (all levels):\n- `notes add`: Add a note.\n- `notes db`: Database maintenance." in md
    assert "- `notes db migrate` (deprecated): Run schema migrations." in md
    assert "## `notes add [OPTIONS] TITLE`" in md
    assert "- `TITLE` (text; required)" in md
    assert "- `--tag TEXT` (repeatable): Tag to attach." in md
    assert "- `--priority [low|high]` (default: low)" in md
    assert "- `--token TEXT` (env: NOTES_TOKEN): API token." in md
    assert "## `notes db migrate [OPTIONS]` (deprecated)" in md
    assert "secret" not in md


def test_skill_has_valid_frontmatter_and_block(tree):
    skill = help2skill.render_skill(tree, name="notes", description='Manage "notes" from the shell.')
    head, _, rest = skill.partition("\n---\n")
    assert head == '---\nname: notes\ndescription: "Manage \\"notes\\" from the shell."'
    assert "<!-- help2skill:begin" in rest and rest.rstrip().endswith("<!-- help2skill:end -->")
    assert "## `notes [OPTIONS] COMMAND [ARGS]...`" in rest


def test_default_description(tree):
    assert help2skill.default_description(tree) == "Use the `notes` command-line tool. Manage notes."


@pytest.mark.parametrize("name", ["Notes", "-notes", "no--tes", "a" * 65, ""])
def test_invalid_skill_names(name):
    with pytest.raises(ValueError):
        validate_skill_metadata(name, "ok")


@pytest.mark.parametrize("description", ["", "x" * 1025, "use <b>this</b>"])
def test_invalid_descriptions(description):
    with pytest.raises(ValueError):
        validate_skill_metadata("notes", description)
