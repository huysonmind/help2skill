"""cyclopts and plumbum adapters."""

from enum import Enum
from typing import Annotated, Literal

import pytest

import help2skill
from help2skill.sync import check_references


class Region(str, Enum):
    eu = "eu"
    us_east = "us-east"


@pytest.fixture
def cyclopts_app():
    cyclopts = pytest.importorskip("cyclopts")
    from pathlib import Path

    app = cyclopts.App(name="ship", help="Deploy things.\n\nLonger text.")
    db = cyclopts.App(name="db", help="Database commands.")
    app.command(db)

    @app.command
    def deploy(
        target: str,
        *,
        region: Region = Region.eu,
        replicas: Annotated[int, cyclopts.Parameter(help="How many.", env_var="REPLICAS")] = 2,
        dry_run: bool = False,
        tag: list[str] | None = None,
        mode: Literal["fast", "safe"] = "safe",
    ):
        """Deploy TARGET.

        Parameters
        ----------
        target: str
            What to deploy.
        dry_run: bool
            Only print.
        """

    @db.command
    def migrate(path: Path, steps: int = 1):
        """Run migrations."""

    @db.command(show=False)
    def secret(): ...

    @app.default
    def main(verbose: bool = False):
        """Root default."""

    return app


def test_cyclopts_tree(cyclopts_app):
    tree = help2skill.introspect(cyclopts_app)
    assert tree.name == "ship"
    assert [c.name for c in tree.subcommands] == ["db", "deploy"]
    db = tree.get("db")
    assert [c.name for c in db.subcommands] == ["migrate"]
    assert db.hidden_subcommands == ["secret"]
    (verbose,) = tree.options
    assert verbose.opts == ["--verbose"] and verbose.secondary_opts == ["--no-verbose"]

    deploy = tree.get("deploy")
    assert deploy.help == "Deploy TARGET."
    params = {p.name: p for p in deploy.params}
    assert params["target"].kind == "argument" and params["target"].required
    assert params["target"].help == "What to deploy."
    assert params["region"].choices == ["eu", "us-east"] and params["region"].default == "eu"
    assert params["replicas"].type == "int" and params["replicas"].envvars == ["REPLICAS"]
    assert params["dry_run"].is_flag and params["dry_run"].secondary_opts == ["--no-dry-run"]
    assert params["tag"].multiple and params["tag"].type == "text"
    assert params["mode"].choices == ["fast", "safe"]

    migrate = db.get("migrate")
    assert [(p.name, p.type, p.required, p.default) for p in migrate.arguments] == [
        ("path", "path", True, None),
        ("steps", "int", False, "1"),
    ]


def test_cyclopts_markdown_and_check(cyclopts_app):
    tree = help2skill.introspect(cyclopts_app)
    text = help2skill.render_markdown(tree)
    assert "## `ship deploy [OPTIONS] TARGET`" in text
    assert "- `--region [eu|us-east]` (default: eu)" in text
    assert check_references("`ship deploy api --region us-east --dry-run`", tree) == []
    problems = check_references("`ship deploy api --region mars --replica 3`", tree)
    assert [p.kind for p in problems] == ["invalid-choice", "unknown-option"]


@pytest.fixture
def plumbum_app():
    cli = pytest.importorskip("plumbum.cli")

    class Geet(cli.Application):
        """Manage a tiny repository.

        More details here.
        """

        PROGNAME = "geet"
        VERSION = "1.7.2"
        verbose = cli.Flag(["-v", "--verbose"], help="Chatty output")
        quiet = cli.CountOf("-q", help="Quieter")
        color = cli.SwitchAttr("--color", cli.Set("auto", "always", "never"), default="auto", help="When")
        jobs = cli.SwitchAttr(["-j", "--jobs"], cli.Range(1, 16), default=2, envname="GEET_JOBS")
        include = cli.SwitchAttr("--include", str, list=True, help="Paths")

        @cli.switch("--log-to-file", str, argname="FILE")
        def log_to_file(self, filename):
            """Log to FILE"""

        def main(self):
            pass

    @Geet.subcommand("commit")
    class GeetCommit(cli.Application):
        """Create a commit"""

        auto_add = cli.Flag("-a", help="Add all files")
        message = cli.SwitchAttr("-m", str, mandatory=True)

        def main(self, path: cli.ExistingFile, *more):
            pass

    @Geet.subcommand("push")
    class GeetPush(cli.Application):
        """Push to remote"""

        def main(self, remote="origin", branch: str = "main"):
            pass

    return Geet


def test_plumbum_tree(plumbum_app):
    tree = help2skill.introspect(plumbum_app)
    assert tree.name == "geet"
    assert tree.short_help == "Manage a tiny repository."
    opts = {p.opts[-1]: p for p in tree.options}
    # -v belongs to --verbose; plumbum's own --version, --help, --help-all are left out.
    assert set(opts) == {"--color", "--include", "--jobs", "--log-to-file", "--verbose", "-q"}
    assert opts["--verbose"].opts == ["-v", "--verbose"] and opts["--verbose"].is_flag
    assert opts["-q"].count
    assert opts["--color"].choices == ["auto", "always", "never"]
    assert opts["--jobs"].range == "1<=x<=16" and opts["--jobs"].envvars == ["GEET_JOBS"]
    assert opts["--include"].multiple
    assert opts["--log-to-file"].metavar == "FILE"

    commit = tree.get("commit")
    assert [(a.name, a.type, a.required, a.multiple) for a in commit.arguments] == [
        ("path", "path", True, False),
        ("more", "text", False, True),
    ]
    message = next(p for p in commit.options if p.opts == ["-m"])
    assert message.required and message.help is None  # plumbum's "Sets an attribute" dropped
    push = tree.get("push")
    assert [(a.name, a.default, a.required) for a in push.arguments] == [
        ("remote", "origin", False),
        ("branch", "main", False),
    ]


def test_plumbum_check(plumbum_app):
    tree = help2skill.introspect(plumbum_app)
    assert check_references("`geet -v --color never commit -a -m 'x' file.txt`", tree) == []
    problems = check_references("`geet --colour never pull`", tree)
    assert [p.kind for p in problems] == ["unknown-option", "unknown-command"]


def test_plumbum_target_loads_from_the_command_line(tmp_path, monkeypatch, capsys):
    pytest.importorskip("plumbum")
    from help2skill.cli import main

    (tmp_path / "geet_app.py").write_text(
        "from plumbum import cli\n\n"
        "class Geet(cli.Application):\n"
        '    """Tiny tool."""\n'
        '    PROGNAME = "geet"\n'
        "    def main(self, name):\n"
        "        pass\n"
    )
    monkeypatch.chdir(tmp_path)
    assert main(["markdown", "geet_app:Geet"]) == 0
    assert "# `geet NAME`" in capsys.readouterr().out


def test_cyclopts_meta_app_options_and_lazy_commands(tmp_path, monkeypatch):
    cyclopts = pytest.importorskip("cyclopts")
    (tmp_path / "lazy_cmds.py").write_text(
        "import cyclopts\n\n"
        "sub = cyclopts.App(name='flow', help='Manage flows.')\n\n"
        "@sub.command\n"
        "def ls(limit: int = 10):\n"
        "    '''List flows.'''\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    app = cyclopts.App(name="pf")
    try:
        app.command("lazy_cmds:sub", name="flow")
    except TypeError:
        pytest.skip("this cyclopts has no lazy commands")

    @app.meta.default
    def meta(
        *tokens: Annotated[str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)], profile: str = ""
    ):
        app(tokens)

    tree = help2skill.introspect(app)
    assert [o.opts for o in tree.options] == [["--profile"]]
    assert [c.path for c in tree.walk()] == [["pf"], ["pf", "flow"], ["pf", "flow", "ls"]]
    assert check_references("`pf --profile dev flow ls --limit 3`", tree) == []
