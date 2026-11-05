from __future__ import annotations

import pytest
from sample_clis import build_parser, notes, typer_app

import help2skill


@pytest.fixture(params=["click", "typer", "argparse"])
def tree(request):
    cli = {"click": notes, "typer": typer_app, "argparse": build_parser()}[request.param]
    return help2skill.introspect(cli, "notes")


def test_same_command_tree_for_every_framework(tree):
    paths = [" ".join(c.path) for c in tree.walk()]
    assert paths == ["notes", "notes add", "notes db", "notes db migrate"]


def test_root_option(tree):
    verbose = next(p for p in tree.options if p.name == "verbose")
    assert verbose.is_flag
    assert set(verbose.opts) == {"--verbose", "-v"}
    assert verbose.help == "Show more output."


def test_add_command_params(tree):
    add = tree.get("add")
    assert add.short_help == "Add a note."
    (title,) = add.arguments
    assert title.name == "title" and title.required
    tag = next(p for p in add.options if p.name in {"tag", "tags"})
    assert tag.multiple and tag.opts == ["--tag"]
    priority = next(p for p in add.options if p.name == "priority")
    assert priority.choices == ["low", "high"]
    assert priority.default == "low"


def test_hidden_things_are_skipped(tree):
    assert tree.get("secret") is None
    names = {p.name for c in tree.walk() for p in c.params}
    assert "llms" not in names
    assert "install_completion" not in names


def test_click_and_typer_details():
    for cli in (notes, typer_app):
        tree = help2skill.introspect(cli, "notes")
        token = next(p for p in tree.get("add").options if p.name == "token")
        assert token.envvars == ["NOTES_TOKEN"]
        assert tree.find(["db", "migrate"]).deprecated
        assert tree.get("add").help.startswith("Add a note.\n\nThe note is stored locally.")


def test_argparse_details():
    tree = help2skill.introspect(build_parser())
    assert tree.name == "notes"
    add = tree.get("add")
    assert "token" not in {p.name for p in add.params}  # help=SUPPRESS
    steps = next(p for p in tree.find(["db", "migrate"]).options if p.name == "steps")
    assert steps.type == "int" and steps.default == "1"
    assert steps.help == "How many steps (default: 1)."


def test_typer_enum_default_is_plain_value():
    tree = help2skill.introspect(typer_app, "notes")
    priority = next(p for p in tree.get("add").options if p.name == "priority")
    assert priority.default == "low"


def test_unknown_object_raises():
    with pytest.raises(TypeError):
        help2skill.introspect(object())
