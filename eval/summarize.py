"""Assignment 1, Parts B to D: build the tables in reports/LAB_01.json from your runs.

Reads every trace in runs/ and the comments in the tracker, decides each run's
success with eval/check_triage.check, and writes the `results` entry for each way
and the computed fields of `analysis` into reports/LAB_01.json.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from eval.check_triage import check
from harness.trace import read_trace
from harness.tracker import Tracker

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "LAB_01.json"
WAYS = ("direct", "workflow", "agent", "hybrid")


def load_runs(issues: set[int]) -> dict[str, list[dict]]:
    runs = {w: [] for w in WAYS}
    for path in sorted((ROOT / "runs").glob("*.jsonl")):
        if path.name.startswith("_"):
            continue
        records = read_trace(path)
        start, end = records[0], records[-1]
        if (start.get("type") != "run_start" or start.get("lab") != "01" or start.get("way") not in WAYS
                or start.get("backend") == "never-stops" or start.get("issue") not in issues
                or end.get("type") != "run_end"):
            continue
        runs[start["way"]].append({
            "run_id": start["run_id"], "issue": start["issue"], "sweep": start["sweep"],
            "model_calls": [r for r in records if r["type"] == "model_call"],
            "tool_calls": [r for r in records if r["type"] == "tool_call"],
            "terminal": next((r["terminal_reason"] for r in records if r["type"] == "end"), None),
            "elapsed_s": end["elapsed_s"],
        })
    return runs


def mean(values):
    return sum(values) / len(values) if values else None


def percentile(values, p):
    """Nearest-rank percentile."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(1, math.ceil(p / 100 * len(ordered))) - 1]


def usage_sum(run, key):
    return sum(c["usage"][key] for c in run["model_calls"])


def summarize_way(runs, passed, issues):
    per_issue_runs, per_issue_pass, per_sweep = Counter(), Counter(), Counter()
    for r in runs:
        per_issue_runs[r["issue"]] += 1
        per_issue_pass[r["issue"]] += passed[r["run_id"]]
        per_sweep[r["sweep"]] += passed[r["run_id"]]
    return {
        "runs": len(runs),
        "passes": sum(passed[r["run_id"]] for r in runs),
        "per_issue": {str(i): per_issue_pass[i] for i in issues},
        "sweep_min": min(per_sweep.values(), default=None),
        "sweep_max": max(per_sweep.values(), default=None),
        "all_ten": sum(1 for i in issues if per_issue_runs[i] >= 10 and per_issue_pass[i] == per_issue_runs[i]),
        "mean_prompt_tokens": mean([usage_sum(r, "prompt_tokens") for r in runs]),
        "mean_output_tokens": mean([usage_sum(r, "output_tokens") for r in runs]),
        "mean_cached_tokens": mean([usage_sum(r, "cache_read_input_tokens") for r in runs]),
        "p50_latency_s": percentile([r["elapsed_s"] for r in runs], 50),
        "p95_latency_s": percentile([r["elapsed_s"] for r in runs], 95),
        "mean_cost_usd": mean([sum(c["cost_usd"] or 0 for c in r["model_calls"]) for r in runs]),
        "mean_tool_calls": mean([len(r["tool_calls"]) for r in runs]),
        "max_tool_calls": max((len(r["tool_calls"]) for r in runs), default=None),
    }


def measured_worst_case(agent_runs):
    firsts = [r["model_calls"][0]["usage"]["prompt_tokens"] for r in agent_runs if r["model_calls"]]
    steps = []
    for r in agent_runs:
        p = [c["usage"]["prompt_tokens"] for c in r["model_calls"]]
        steps += [b - a for a, b in zip(p, p[1:])]
    return mean(firsts), mean(steps)


def main() -> None:
    answers = yaml.safe_load((ROOT / "fixtures" / "answers.yaml").read_text())["eval"]
    issues = sorted(answers)
    tracker = Tracker(ROOT)
    runs = load_runs(set(issues))
    report = json.loads(REPORT.read_text())

    passed, results = {}, {}
    for way in WAYS:
        for r in runs[way]:
            passed[r["run_id"]] = check(tracker, r["run_id"], r["issue"], answers[r["issue"]])
        if runs[way]:
            results[way] = summarize_way(runs[way], passed, issues)
            report["results"][way] = results[way]

    a = report["analysis"]
    if "direct" in results and "agent" in results:
        tok = lambda w: results[w]["mean_prompt_tokens"] + results[w]["mean_output_tokens"]
        a["ratio_agent_over_direct_tokens"] = tok("agent") / tok("direct")
    if "workflow" in results and "agent" in results:
        c = results["workflow"]["mean_cost_usd"]
        m = results["agent"]["mean_cost_usd"] / c
        wins = sum(1 for i in issues
                   if results["workflow"]["per_issue"][str(i)] < 5 and results["agent"]["per_issue"][str(i)] >= 5)
        f = wins / len(issues)
        a.update(m_agent_over_workflow_cost=m, f=f, blended_cost=c * ((1 - f) + f * m),
                 all_agent_cost=c * m, workflow_cost=c)
    if runs["agent"]:
        seqs = Counter(tuple(t["name"] for t in r["tool_calls"]) for r in runs["agent"])
        a["path_entropy"] = {"distinct_sequences": len(seqs),
                             "top3_share": sum(n for _, n in seqs.most_common(3)) / len(runs["agent"])}
        print("agent tool-call sequences:")
        for seq, n in seqs.most_common(8):
            print(f"  {n:>3} x {' > '.join(seq)}")
    if runs["hybrid"]:
        a["hybrid_handoffs"] = sum(1 for r in runs["hybrid"] if r["terminal"] != "completed")
    if "--worst-case" in sys.argv and runs["agent"]:
        F, A = measured_worst_case(runs["agent"])
        N = report["worst_case"]["N"]
        report["worst_case"] = {"F": round(F, 1), "A": round(A, 1), "N": N,
                                "cumulative_prompt_tokens": round(N * F + A * N * (N - 1) / 2)}

    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    for way, s in results.items():
        print(f"{way:<9} {s['passes']}/{s['runs']} passes  per issue {s['per_issue']}  sweeps {s['sweep_min']}-{s['sweep_max']}"
              f"  all_ten {s['all_ten']}  ${s['mean_cost_usd']:.5f}/run  tools {s['mean_tool_calls']:.1f}")
    # Per-issue pass rate by way, to see where each way fails.
    by = defaultdict(dict)
    for way in results:
        for i, n in results[way]["per_issue"].items():
            by[i][way] = n
    print("wrote", REPORT.relative_to(ROOT))


if __name__ == "__main__":
    main()
