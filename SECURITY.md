# Security policy

## Supported versions
help2skill is in alpha. Only the latest release receives fixes.

## Reporting a vulnerability
Please report privately through GitHub:
**Security → Report a vulnerability** on https://github.com/huysonmind/help2skill
(private vulnerability reporting). Do not open a public issue.

You should get a first answer within 7 days.

## What help2skill executes
- `help2skill markdown|skill|check <module:attr>` **imports your module** to read the
  command tree, exactly like running your CLI would. Only point it at code you trust.
- If `attr` is a plain function (for example `build_parser`), it is **called** to obtain
  the parser.
- The `--llms` flag only reads the command tree that is already loaded; it does not run
  any command callback.

## Data in generated files
Generated Markdown copies your CLI's help text verbatim. If help text is computed at
runtime (for example a default path under your home directory), that value ends up in
the output. Review `SKILL.md` before committing it.

## Releases
Releases are published to PyPI from GitHub Actions with
[trusted publishing](https://docs.pypi.org/trusted-publishers/); no long-lived API
token is stored anywhere.
