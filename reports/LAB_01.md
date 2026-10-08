# Assignment 1 report · Four ways to triage an issue

Every number here also goes in `reports/LAB_01.json`, which the checker reads
(format: `checks/FORMATS.md`, section 7). Give each number its run count. Mark
any vendor figure you cite with its source type and date.

## Part 0 · The recorded trace
Model calls, tool calls, prompt tokens and the cached share, first and last
prompt size, cumulative over first. One sentence on what the growth means.

The recorded run made 21 model calls and 23 tool calls; it read 399,123 prompt tokens in total, 97.3% of them cache reads (388,338). The first call's prompt was 13,445 tokens and the last was 24,188, so the cumulative prompt tokens were 29.7× the first prompt.

**What the growth means:** every step re-sends the whole history, so the prompt grows with each step and the total grows roughly with the square of the step count (21 steps cost about 30 first-prompts, not 21), which is why a bound on steps is a bound on money; the 97.3% cache share only makes the repeated reading cheaper, it does not remove it.

## Part A · Your loop's bounds
Your three bounds and why. Your worst case: *F*, *A*, *N*, and the cumulative
prompt tokens at your turn limit.

## Part B · Results
The table for all three ways: passes out of 60, per issue out of 10, the spread
(lowest and highest sweep), issues solved in every run, tokens, p50 and p95
latency, cost, tool calls.

## Part C · The decision
1. Find the diamond, for each way.
2. Your multipliers, and two differences from the vendor's 4×.
3. *f*, the blended cost, and the comparison with all-agent and all-workflow;
   then the slide's version, with *c*, *m* and *f* against the direct call.
4. Path entropy.
5. The four gates, one line of evidence each, and your verdict: agent,
   workflow or hybrid. If hybrid, where the line sits.
6. Your predictions: each one in `reports/PREDICTIONS_01.md` that missed, what
   you believed, and which trace shows why it was wrong.
7. The seven-layer audit: how many layers are empty (`ARCHITECTURE.md`).

## Part D · The hybrid

### Hand-off rule (written before the hybrid was measured)

**Rule:** run the workflow's read, extract, search and choose steps. If the choice is labelled `bug`, `feature` or unparseable, and its file is not under `src/`, hand the issue to the agent (`ways/hybrid.py`, `should_hand_off`). Otherwise post the workflow's comment.

**Traces behind it** (60 workflow runs, rules replayed offline: search is deterministic, so I re-ran each trace's queries):

| Candidate rule | Where it fires | Verdict |
|---|---|---|
| any search returned `No matches.` | 4202 (10/10 runs, all fail), 4204 (10 runs: 7 fail, 2 pass, 1 other), 4205 (8 runs, all pass), 4206 (9 runs, all fail) | fires on passing runs (4205, two 4204 runs), too many hand-offs |
| chosen file appears in none of the search results | 4203 (6 runs, all pass), 4206 (10 runs, fail), 4202 (1) | fires on the 6 passing 4203 runs: wrong direction |
| bug/feature answer with a file outside `src/` (**chosen**) | 4202 (9 of 10 runs, picked `docs/ARCHITECTURE.md`, all fail); nowhere on any passing run | no false hand-offs, cheap |

**What the rule cannot do:** the workflow's only partial success is 4203 (6/10), where the 4 failed runs picked an `src/api/` file instead of the parser; their search results look the same as the 6 passing runs' (same token counts), so the miss is in the choose call and no rule that reads the searches can see it. The rule also fires on 4202, where Part B shows the agent scored 0/10. So I expect the hybrid to cost about the workflow and pass about as many runs as the workflow (28/60), not more. The rule was chosen from the same six issues it is measured on, so its result is optimistic.

Your hand-off rule, and the Part B traces that led you to it (written before you
measure). Its row beside the three ways (the same columns as Part B's table), how many of
its runs handed the issue to the agent, and its measured cost per run beside your
blended cost from Part C, item 3. Does it change your Part C verdict? Which of
the four would you ship, and why?

## Assistance
Which AI tool, what it wrote, what you checked.
