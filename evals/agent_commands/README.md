# Do agents write correct commands with a generated SKILL.md?

A small experiment, run on 2026-11-07. Treat it as a first signal, not a benchmark.

## Setup

- Two real CLIs: [llm](https://github.com/simonw/llm) 0.37.1 and
  [sqlite-utils](https://github.com/simonw/sqlite-utils) 4.2.1.
- 8 tasks each ([`tasks_llm.md`](tasks_llm.md), [`tasks_sqlite.md`](tasks_sqlite.md)),
  chosen to need specific options; some use recent features (`llm openai endpoint add`).
- Three conditions, each run once with Claude Sonnet and once with Claude Haiku, as
  Claude Code subagents:
  - **memory**: answer from what the model knows; no commands, no files.
  - **help**: may run `<cli> … --help` as often as it likes.
  - **skill**: given the `SKILL.md` that help2skill generated ([`skills/`](skills)); may
    still run `--help`.
- Grading ([`grade.py`](grade.py)): each answer is parsed by the real Click CLI with
  `make_context` (nothing runs), then the parsed parameters are compared with the task.
  Both `sqlite-utils rows …` and an equivalent `sqlite-utils query …` count for task 5.

## Results

| Condition | Correct (of 32) | `--help` calls | Time per CLI run |
|---|---:|---:|---:|
| memory | 28 | 0 | 11–17 s |
| help | 31 | 65 (8–28 per run) | 13–42 s |
| skill | **32** | **0** | 13–28 s |

Per run ([`results.txt`](results.txt)):

| Run | memory | help | skill |
|---|---|---|---|
| llm, Sonnet | 7/8 | 7/8, 19 help calls, 36 s | 8/8, 0 calls, 13 s |
| llm, Haiku | 6/8 | 8/8, 28 help calls, 42 s | 8/8, 0 calls, 13 s |
| sqlite-utils, Sonnet | 8/8 | 8/8, 8 help calls, 13 s | 8/8, 0 calls, 14 s |
| sqlite-utils, Haiku | 7/8 | 8/8, 10 help calls, 32 s | 8/8, 0 calls, 28 s |

What failed:
- `llm openai endpoint add` (added in a recent llm release) was missed by both memory
  runs and by Sonnet even with `--help`: it wrote a YAML file by hand instead.
- From memory, Haiku wrote `llm schema …` (no such command; llm runs it as a prompt
  and rejects `--multi`) and `sqlite-utils convert … --code` (no such option).

## Reading

- With a generated SKILL.md, agents got every task right without exploring the CLI.
  An agent that explores with `--help` gets nearly the same accuracy, but needs 8–28
  extra calls and up to three times longer on the larger CLI (llm).
- Token use was about the same in all conditions: reading the skill costs roughly what
  the `--help` calls cost.
- The gap is largest for features newer than the model (`llm openai endpoint add`)
  and for the smaller model.

## Limits

16 tasks, one run per cell, two well-known CLIs, two models. Agents were told the CLI
exists and were allowed to look things up; agents in the wild often guess instead
(the memory condition). Run it again with more tasks and repetitions before quoting
these numbers as general.
