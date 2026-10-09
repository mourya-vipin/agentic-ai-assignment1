# ARCHITECTURE.md · RepoMind on the seven layers

Assignment 1, Part C item 7 (Week 1, slide 43). For each layer: what does this job,
and where is it enforced. Cite code as a file path and line number joined by a
colon, inside backticks; the checker opens every reference. A layer held only by a
sentence in a prompt (any file under `prompts/`) is **EMPTY**, and so is a layer
nothing does yet. Status is one of: present, partial (say what is missing), or
**EMPTY**.

| Layer | What does this job | Where it is enforced | Status |
|---|---|---|---|
| Model | `gemini-3.5-flash-lite` reasons, picks tools and writes the label and file; named once, with its provider, in settings; the call goes out through the OpenAI-compatible backend | `settings.yaml:24`, `harness/backends.py:212` | present |
| Harness | The loop that calls the model, runs the tools it asks for, appends the turns and stops on a bound | `agent/loop.py:74`, `agent/loop.py:86` | present (no history trimming: runs are short, at most 12 steps) |
| Tools | `read_issue`, `search_repo` and `post_comment`, run through one registry that turns expected failures into error results; `post_comment` is the only write | `tools/__init__.py:60`, `tools/post_comment.py:25` | present |
| Memory & State | Nothing survives a run except the tracker's comment log; within a run the message list is the only state, and nothing remembers earlier triages or reporters | `agent/loop.py:57` (the in-run message list only) | **EMPTY** |
| Control & Policy | Three outside limits (steps, tokens, wall clock) end any agent run; a per-run and a per-lab token ceiling stop spend; one comment per run is checked afterwards | `agent/loop.py:63`, `agent/loop.py:66`, `agent/loop.py:69`, `harness/client.py:118`, `harness/runner.py:148` | partial: limits cost and time only; nothing limits *what* the agent may do (it can post any text to any issue, publicly) and no person approves a comment before it lands |
| Observability | Every model call and tool call is written to a trace line with tokens, cost, latency and the terminal reason | `harness/trace.py:38`, `harness/trace.py:52`, `harness/trace.py:65` | present |
| Evaluation | Success is read from the tracker by run_id, never from the model; the results script recomputes every table from traces | `eval/check_triage.py:13`, `eval/summarize.py:97` | partial: an offline measurement on six issues after the fact; no pre-release gate, no regression test, nothing runs in production |

**Empty layers:** 1 of 7 (Memory & State), with two partial (Control & Policy, Evaluation). Slide 46 expects four to be missing from a first build: memory and state, control and policy, observability, and evaluation. Mine is better on observability and evaluation because the starter harness supplied a trace writer, a metered client and a grounded check, and I wrote the loop, bounds and results script; it is the same on memory, and control and policy is only half built.
