"""Grade answers by parsing them with the real Click CLI (nothing is executed).

    uv run --no-project --with llm==0.37.1 --with sqlite-utils==4.2.1 \
        python evals/agent_commands/grade.py
"""

import glob
import json
import os
import shlex
import tempfile

import click
import llm.cli
import sqlite_utils.cli

HERE = os.path.dirname(os.path.abspath(__file__))


def parse(cli, prog, line):
    """Return (command path, parsed parameters) for ``line``, as the CLI would see them."""
    tokens = shlex.split(line)
    if not tokens or tokens[0] != prog:
        raise ValueError("does not start with the program name")
    args, cmd, name, parent, path = tokens[1:], cli, prog, None, []
    while True:
        ctx = cmd.make_context(name, list(args), parent=parent)
        if not isinstance(cmd, click.Group):
            return tuple(path), ctx.params
        protected = ctx._protected_args if hasattr(ctx, "_protected_args") else ctx.protected_args
        rest = protected + ctx.args
        if not rest:
            return tuple(path), ctx.params
        sub_name, cmd, args = cmd.resolve_command(ctx, rest)
        name, parent = sub_name, ctx
        path.append(sub_name)


def has(values, item):
    return values is not None and item in values


def name_of(value):
    return os.path.basename(str(getattr(value, "name", value)))


# Task number -> (command path, check of the parsed parameters), or a list of alternatives.
LLM = {
    "1": (
        ("openai", "endpoint", "add"),
        lambda p: (
            p["url"] == "http://localhost:8000/v1"
            and p["model_name"] == "qwen3-32b"
            and has(p["aliases"], "qwen")
            and p["key_name"] == "local"
            and p["supports_tools"]
        ),
    ),
    "2": (
        ("logs", "list"),
        lambda p: p["count"] == 5 and p["model"] == "gpt-4o-mini" and p["json_output"] and p["usage"],
    ),
    "3": (
        ("embed-multi",),
        lambda p: (
            p["collection"] == "docs"
            and any(d.rstrip("/") in ("docs", "./docs") and g == "**/*.md" for d, g in p["files"])
            and p["store"]
        ),
    ),
    "4": (
        ("similar",),
        lambda p: (
            p["collection"] == "docs" and p["content"] == "rate limits" and p["number"] == 3 and p["plain"]
        ),
    ),
    "5": (
        ("models", "options", "set"),
        lambda p: p["model"] == "gpt-4o" and p["key"] == "temperature" and p["value"] == "0.2",
    ),
    "6": (
        ("prompt",),
        lambda p: (
            p["prompt"] == "summarize this"
            and has(p["fragments"], "notes.txt")
            and p["system"] == "Be brief"
            and p["no_log"]
            and p["usage"]
        ),
    ),
    "7": (("schemas", "dsl"), lambda p: p["input"] == "name, age int" and p["multi"]),
    "8": (("fragments", "set"), lambda p: p["alias"] == "readme" and p["fragment"] == "README.md"),
}

SQLITE = {
    "1": (
        ("insert",),
        lambda p: (
            p["table"] == "people"
            and name_of(p["file"]) == "people.csv"
            and p["csv"]
            and has(p["pk"], "id")
            and p["replace"]
            and p["no_detect_types"]
        ),
    ),
    "2": (
        ("transform",),
        lambda p: (
            p["table"] == "orders"
            and ("amt", "amount") in p["rename"]
            and any(c in ("amt", "amount") and t.upper() == "FLOAT" for c, t in p["type"])
            and has(p["drop"], "tmp")
            and p["sql"]
        ),
    ),
    "3": (
        ("extract",),
        lambda p: (
            p["table"] == "places"
            and set(p["columns"]) == {"country", "region"}
            and p["other_table"] == "locations"
            and p["fk_column"] == "location_id"
        ),
    ),
    "4": (
        ("enable-fts",),
        lambda p: (
            p["table"] == "articles"
            and set(p["column"]) == {"title", "body"}
            and p["fts5"]
            and p["tokenize"] == "porter"
            and p["create_triggers"]
        ),
    ),
    "5": [
        (
            ("rows",),
            lambda p: (
                p["dbtable"] == "events"
                and set(p["column"]) == {"id", "created"}
                and ":s" in (p["where"] or "")
                and ("s", "failed") in p["param"]
                and " ".join((p["order"] or "").lower().split()) == "created desc"
                and p["limit"] == 10
                and p["table"]
            ),
        ),
        (
            ("query",),
            lambda p: (
                all(
                    x in p["sql"].lower()
                    for x in ("events", ":s", "created desc", "limit 10", "id", "created")
                )
                and "select *" not in p["sql"].lower()
                and ("s", "failed") in p["param"]
                and p["table"]
            ),
        ),
    ],
    "6": (
        ("memory",),
        lambda p: (
            [name_of(x) for x in p["paths"]] == ["a.csv", "b.csv"]
            and "join" in p["sql"]
            and name_of(p["save"]) == "out.db"
        ),
    ),
    "7": (
        ("convert",),
        lambda p: (
            p["table"] == "posts"
            and tuple(p["columns"]) == ("title",)
            and "upper" in p["code"]
            and p["output"] == "title_upper"
            and p["dry_run"]
        ),
    ),
    "8": (
        ("create-index",),
        lambda p: (
            p["table"] == "users"
            and tuple(p["column"]) == ("email",)
            and p["unique"]
            and p["name"] == "idx_users_email"
            and p["if_not_exists"]
        ),
    ),
}


def grade(answers, prog, cli, spec):
    score, notes = 0, []
    for task, alternatives in spec.items():
        alternatives = alternatives if isinstance(alternatives, list) else [alternatives]
        try:
            path, params = parse(cli, prog, answers.get(task, ""))
        except click.UsageError as exc:
            notes.append(f"{task}: rejected by the CLI: {exc.format_message()[:90]}")
            continue
        except Exception as exc:
            notes.append(f"{task}: {exc}"[:120])
            continue
        checks = [check for want, check in alternatives if want == path]
        if not checks:
            notes.append(f"{task}: wrong command `{' '.join(path) or prog}`")
        elif checks[0](params):
            score += 1
        else:
            notes.append(f"{task}: wrong or missing options")
    return score, notes


def main():
    os.chdir(tempfile.mkdtemp())  # click.File / click.Path arguments must exist
    for name in ("people.csv", "a.csv", "b.csv", "notes.txt", "README.md", "data.db"):
        open(name, "w").close()
    for pattern, prog, cli, spec in (
        ("llm_*.json", "llm", llm.cli.cli, LLM),
        ("sqlite_*.json", "sqlite-utils", sqlite_utils.cli.cli, SQLITE),
    ):
        for path in sorted(glob.glob(os.path.join(HERE, "answers", pattern))):
            with open(path) as f:
                score, notes = grade(json.load(f), prog, cli, spec)
            print(f"{os.path.basename(path)}: {score}/{len(spec)}")
            for note in notes:
                print("   ", note)


if __name__ == "__main__":
    main()
