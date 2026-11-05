# Contributing

Thanks for helping! Bug reports, new framework adapters and real-world drift cases
are especially welcome.

## Setup
```console
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

## Pull requests
- One topic per PR, with a test that fails without the change.
- The generated Markdown format is a public contract (users commit it and the drift
  check compares it verbatim). If your change alters output, say so in the PR and add a
  `CHANGELOG.md` entry.
- Keep runtime dependencies at zero.

## Sign-off (DCO)
By contributing you agree that your contribution is licensed under the project's
[MIT license](LICENSE) and that you have the right to submit it, as described in the
[Developer Certificate of Origin](https://developercertificate.org/).
Sign each commit with `git commit -s`, which adds a `Signed-off-by:` line.

## AI-assisted contributions
AI tools are welcome. Mention them in the PR description, and make sure you have read
and understood every line you submit. This project itself was built with AI assistance
(Claude).
