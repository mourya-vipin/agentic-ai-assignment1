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

| Bound | Value | Why |
|---|---|---|
| `max_steps` | 12 | the task needs read, 2 to 4 searches, post (about 6 calls); 12 is twice that, and the worst case grows with N² |
| `max_tokens` | 80,000 | about twice the 12-step worst case; a backstop far under the 400,000 harness ceiling, so my loop, not the harness, ends a runaway run |
| `wall_clock_s` | 300 | 12 calls take about a minute; 300 s leaves room for free-tier rate-limit waits (the vendor allows 15 requests a minute) |

All three are checked in code before every model call (`agent/loop.py`), and the harness names the ending with `trace.end`. `make bounds-smoke` (the scripted never-stopping model, free) ends both dev runs on **`turn_limit`**, after exactly 12 model calls and 15,960 tokens: my 80,000-token budget does not bind first, so the step limit is the binding bound.

**Worst case.** Estimated before any run, from my system prompt (~450 tokens) and the three tool definitions (~250): F ≈ 900, A ≈ 450, N = 12, so N·F + A·N(N−1)/2 = 10,800 + 29,700 = **40,500** prompt tokens. Measured on the 60 evaluation agent runs: F = 569, A = 144.1, N = 12, giving **16,336** prompt tokens (`reports/LAB_01.json`, `worst_case`). I over-estimated because search results are short (at most 10 one-line hits) and my prompt is smaller than I guessed. The measured token budget never binds: the step limit does.

**How the 60 agent runs ended:** 57 `model_stopped` (the model posted and said "done"), 1 `turn_limit` (issue 4206, 12 steps), 2 `wall_clock` (rate-limit waits on the free tier). None reached `token_budget`. The turn_limit run made 12 tool calls (the maximum); the mean was 5.2.

## Part B · Results

Model `gemini-3.5-flash-lite` (free tier, priced at the paid rates read on 2026-10-07 from ai.google.dev/gemini-api/docs/pricing: $0.30 / $2.50 / $0.03 per million input / output / cached tokens). 60 runs per way (6 issues × 10 sweeps). Cached tokens were 0 in every run: the vendor reported no cache reads.

| | Direct | Workflow | Agent | Hybrid |
|---|---|---|---|---|
| Passes /60 | **34** | 28 | 30 | 32 |
| Per issue, /10 (4201, 4202, 4203, 4204, 4205, 4206) | 5, 9, 10, 0, 10, 0 | 10, 0, 6, 2, 10, 0 | 10, 0, 10, 0, 10, 0 | 10, 0, 9, 3, 10, 0 |
| Spread: lowest, highest sweep (of 6) | 2, 4 | 2, 4 | 3, 3 | 2, 4 |
| Issues correct in all 10 runs | 2 | 2 | 3 | 2 |
| Mean prompt tokens | 1,093 | 1,259 | 6,200 | 2,128 |
| Mean output tokens | 12.0 | 19.6 | 106.3 | 36.2 |
| Mean cached tokens | 0 | 0 | 0 | 0 |
| Latency p50 / p95 (s) | 0.63 / 1.67 | 1.74 / 50.0 | 21.5 / 89.8 | 26.3 / 142.2 |
| Mean cost per run | $0.000358 | $0.000427 | $0.002126 | $0.000729 |
| Tool calls, mean / max | 2.0 / 2 | 6.0 / 6 | 5.2 / 12 | 6.6 / 12 |

Notes on the methodology. (1) Latency includes the wait my vendor's rate limit imposes, which is why the workflow and hybrid p95s (50 s, 142 s) are far above their p50s: a few runs waited about a minute. Cost and tokens are not affected. (2) Ten runs failed with Google 503 "high demand" errors before any model output (1 agent, 9 hybrid). I got instructor's approval to retry those slots; the failed traces are kept in `runs/_outage/` and every retried slot is a normal run in `runs/`. (3) The agent's spread is 3 to 3 because it solves the same three issues (4201, 4203, 4205) in every run and none of the others: its per-issue results are 10 or 0, never in between.

## Part C · The decision

**1. The diamond.** None of the four has a person approving each step. *Direct:* there is no next step to pick; my code ends the run, so it is a script around one model call. *Workflow:* my code picks every step (read, extract, search per term, choose, post) and ends the run; the model fills each step in. *Agent:* the model picks the next tool and decides when it is done ("done" after post_comment), though my code bounds it from outside and ends the run for any bound. *Hybrid:* per component, the first half is a workflow; the decision to hand off is mine (`ways/hybrid.py`); and after a hand-off the agent's component decides. A system is rarely one label, and this one is two.

**2. Multipliers.** Agent tokens per run (prompt plus output) 6,307 over direct's 1,105 = **5.7×**, against the lecture's ≈4× (slide 30, Anthropic-reported, one team, its own workload, 2025). Two differences: (a) their comparison is an agent against a *chat interaction* on real work with long documents and code, while my "direct" call carries a fixed 1,100-token repository summary and no tools, so the agent's multiplier is measured against a very small base; (b) my agent runs are short (5 tool calls, a 570-token first prompt) and nothing is cached, while theirs run long enough for history to dominate and for caching to discount it (Part 0 shows 97% cache reads on a long run). Cost: agent $0.002126 over workflow $0.000427 gives **m = 4.98**. (Against direct, the cost multiplier is 5.9.)

**3. Where the agent earns it.** f = the share of issues where the workflow passes fewer than 5 of 10 and the agent passes 5 or more. Workflow below 5: 4202 (0), 4204 (2), 4206 (0). The agent is at 5 or more on none of them (0, 0, 0). So **f = 0**. Blended cost c × [(1 − f) + f × m] = c = **$0.000427**; all-agent c × m = **$0.002126**; workflow alone $0.000427. With f = 0 the blended cost is just the workflow's cost. The cost of each extra correct triage, agent over workflow: extra cost per run $0.001699 divided by extra passes per run (30 − 28)/60 = 0.033 gives **$0.051 per extra correct triage**, and the agent is still worse than direct (34 passes at a sixth of the cost). The one issue where the agent beats the workflow is 4203 (10/10 against 6/10), which is exactly the issue the workflow already gets right more often than not, so f does not see it; the agent loses 4204 (0 against 2). The slide's version, with c, m, f against the direct call: c = $0.000358, m = 5.94, and direct passes fewer than 5 on 4204 and 4206 (0, 0) where the agent also passes 0, so f = 0 and the blended cost is $0.000358. The two baselines give the same f; gate 4 should use the workflow-or-direct baseline you would actually ship if the agent lost, which here is the direct call (cheaper *and* 6 passes better than my workflow). The slide's "one plain call" is the right baseline for this data.

**4. Path entropy.** Across the agent's 60 runs: **10 distinct tool sequences**; the top three cover 38 of 60 runs (**63.3%**). Every sequence has the same shape, read_issue, then 1 to 7 searches, then post_comment; the only thing that varies is how many searches. That variation does not buy correctness: each issue is solved either 10 times or 0 times, whatever the path (4204 takes the longest paths, 7 to 10 tool calls, and fails every time). The part that is not earning its cost is the agent's adaptive search loop: a fixed read, search, post workflow would produce nearly the same paths, and the extra searches only re-send a growing prompt.

**5. The four gates.** (1) *Does the task vary case to case?* Barely: all six issues go through the same read, search, answer path, and the agent's own paths show it. (2) *Can you limit the damage of a mistake?* Yes: the one write is a triage comment, one per run, bounded by three outside limits; a wrong label is a nuisance, not an incident. (3) *Will you catch it in time?* No: nobody reads the comment before it lands in a public issue; only measurement after, which is what slide 11 warns about. (4) *Is it worth the multiplier?* No: 5× the cost (m = 4.98) for 2 more passes than the workflow and 4 fewer than direct. **Verdict: workflow** (code owns control flow). On my numbers the best shippable design is the simplest one, the direct call, which is the degenerate workflow (one step, my code decides); the extract-search-choose workflow was *worse* than it because search results are dominated by docs and changelog lines, and the choose step trusts them.

**6. Predictions that missed** (`reports/PREDICTIONS_01.md`).
- *Agent, predicted 42 of 60, got 30.* I believed adaptive search would find files the issue does not name. The traces say it stops at the first plausible file: on 4202 (`agent-4202-s01-72d8f0`) it searched CSV and xlsx, never found the export-format module, and guessed an API file; on 4204 (`agent-4204-s01-19006d`) it found the rollup email file and stopped, never reaching the date helper that causes the bug (the tools can only search, not read a file, so it cannot follow an import); on 4206 (`agent-4206-s01-6242f0`) it ran one search and posted the file named in the issue title, which is wrong.
- *Workflow, predicted 36, got 28.* I expected fixed searches to find real code. On 4202 (`workflow-4202-s01-3aa780`) four searches for export, csv, format, tsv returned changelog, readme and docs lines, and the choose call picked `docs/ARCHITECTURE.md` in 9 of 10 runs.
- *Direct, predicted 30, got 34*, the closest: its fixed summary lists the export-format module by name, so it finds the right file for 4202 (9/10); it split 5/10 on 4201 (password-reset email), choosing the auth file half the time.
- *Hardest issue.* I predicted 4206 for all, and it was 0/10 for every way (right). But I predicted the agent's hardest would be 4203; it is 10/10 there and fails 4202, 4204, 4206.
- *Order.* I expected agent > workflow > direct on success. The measured order is direct > hybrid > agent > workflow.

**7. Seven-layer audit.** See `ARCHITECTURE.md`: 1 layer is EMPTY (Memory & State), 2 are partial (Control & Policy, Evaluation), 4 present. Slide 46 expects four missing from a first build; mine has fewer because the starter harness already supplies the model client, the trace and the check, and I built the loop, bounds and results script on top. What is still missing is what slide 46 predicts matters: nothing remembers across runs, the only policy is cost, time and steps (nothing stops the model posting somewhere it should not), and evaluation is an offline run on six issues, not a release gate.

## Part D · The hybrid

### Hand-off rule (written before the hybrid was measured)

**Rule:** run the workflow's read, extract, search and choose steps. If the choice is labelled `bug`, `feature` or unparseable, and its file is not under `src/`, hand the issue to the agent (`ways/hybrid.py`, `should_hand_off`). Otherwise post the workflow's comment.

**Traces behind it** (60 workflow runs, rules replayed offline: search is deterministic, so I re-ran each trace's queries):

| Candidate rule | Where it fires | Verdict |
|---|---|---|
| any search returned `No matches.` | 4202 (10/10 runs, all fail), 4204 (10 runs: 7 fail, 2 pass, 1 other), 4205 (8 runs, all pass), 4206 (9 runs, all fail) | fires on passing runs (4205, two 4204 runs), too many hand-offs |
| chosen file appears in none of the search results | 4203 (6 runs, all pass), 4206 (10 runs, fail), 4202 (1) | fires on the 6 passing 4203 runs: wrong direction |
| bug/feature answer with a file outside `src/` (**chosen**) | 4202 (9 of 10 runs, picked `docs/ARCHITECTURE.md`, all fail); nowhere on any passing run | no false hand-offs, cheap |

**What the rule cannot do:** the workflow's only partial success is 4203 (6/10), where the 4 failed runs picked an `src/api/` file instead of the parser; their search results look the same as the 6 passing runs' (same token counts), so the miss is in the choose call and no rule that reads the searches can see it. The rule also fires on 4202, where Part B shows the agent scored 0/10. So I expected the hybrid to cost about the workflow and pass about as many runs as the workflow (28/60), not more. The rule was chosen from the same six issues it is measured on, so its result is optimistic.

### Measured

Its row is in Part B's table: **32/60** passes (workflow 28, agent 30, direct 34), $0.000729 per run (workflow $0.000427, agent $0.002126), 10 of 60 runs handed the issue to the agent (`hybrid_handoffs` = 10; counted from the `end` records that are not `completed`).

**Where the hand-offs landed:** 8 on issue 4202 (the agent then failed every one: 0 passes), 2 on issue 4203 (both passed). None elsewhere. Part C's f = 0 said the agent earns its cost nowhere by the 5-of-10 test, and the hand-offs mostly went to the issue where the agent was 0/10, so the rule mostly spent agent money on a lost cause. The two 4203 hand-offs are the only hand-offs that paid.

**Measured cost against the Part C blended cost.** Blended cost was $0.000427 (equal to the workflow's, because f = 0). Measured is $0.000729, **71% higher**. The gap is the 10 hand-offs: each pays for the workflow's work *and then* the agent's whole run, which re-reads the issue and searches again; (0.000729 − 0.000427) × 60 / 10 = $0.0018 per hand-off, close to a whole agent run ($0.0021). The blended formula assumed free hand-offs for the right issues; a real rule pays the workflow even for the issues it passes on.

**Is the 32 against 28 a real gain?** No. The sweep ranges overlap (workflow 2 to 4, hybrid 2 to 4 passes of 6), and where the hybrid gained, it was luck on the *workflow* half: on 4203 the 8 non-hand-off runs passed 7 times (88%), against 6 of 10 in the workflow's own measurement, with identical code and prompts; 4204 went 2 to 3 the same way. The hand-offs themselves added +0 on 4202 and +2 on 4203.

**Does it change the Part C verdict?** No. The hybrid is cheaper than the agent and about equal to the workflow on success, but still worse than the direct call (34 at $0.000358). **I would ship the direct call**, the simplest design where my code owns the control flow, and I would put work into what actually fails: all four designs miss 4206 (issue names the wrong file) and 4204 (cause is a helper, not the file the symptom shows), which needs a tool that reads files and follows imports (Week 3's tool rewrite), not more autonomy. Final verdict in `analysis.verdict`: **workflow**.

## Assistance

Claude Code (Claude Sonnet 5.5) wrote some code in `eval/`, `agent/`, `ways/` and `prompts/` and drafted this report and `ARCHITECTURE.md`. I ran every measurement in terminal with my own API key, chose the model setup, pushed the predictions before the evaluation runs, and was told by instructor to retry the outage runs. What I checked: `make test` and `make check-01` pass; `make bounds-smoke` ends on `turn_limit`; the results table is generated by `eval/summarize.py` from `runs/` and the tracker, never typed by hand; I read the per-issue traces behind every claim in Part C.
