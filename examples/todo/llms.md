# `todo COMMAND [ARGS]...`

Keep a to-do list in a local file.

Commands (all levels):
- `todo add`: Add a task.
- `todo finish`: Mark a task as done.
- `todo list`: List tasks.
- `todo tag`: Manage tags.
- `todo tag rename`: Rename a tag on every task.

## `todo add [OPTIONS] TEXT`

Add a task.

Arguments:
- `TEXT` (text; required)

Options:
- `--priority [low|normal|high]` (default: normal)
- `-t, --tag TEXT` (repeatable): Tag to attach.
- `--due TEXT` (env: TODO_DUE): Due date, YYYY-MM-DD.

## `todo finish TASK_ID`

Mark a task as done.

Arguments:
- `TASK_ID` (int; required)

## `todo list [OPTIONS]`

List tasks.

Options:
- `--done / --open` (default: false): Show finished or open tasks.
- `--limit INT` (range: 1<=x<=500; default: 20): Maximum tasks to show.

## `todo tag COMMAND [ARGS]...`

Manage tags.

Commands:
- `todo tag rename`: Rename a tag on every task.

## `todo tag rename OLD NEW`

Rename a tag on every task.

Arguments:
- `OLD` (text; required)
- `NEW` (text; required)
