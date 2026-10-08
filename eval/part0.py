"""Assignment 1, Part 0: read the recorded run and measure how the prompt grew.

No API calls. Counts model calls by distinct message.id (one call can span
several assistant lines), and a call's prompt tokens are its input_tokens plus
cache_read_input_tokens plus cache_creation_input_tokens.

"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDING = ROOT / "fixtures" / "week01_recorded_run.jsonl"
REPORT = ROOT / "reports" / "LAB_01.json"


def prompt_tokens(usage: dict) -> int:
    return (usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0))


def measure(path: Path = RECORDING) -> dict:
    calls: dict[str, dict] = {}   # message.id -> usage, in first-seen order
    tool_calls = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("type") != "assistant":
            continue
        message = record["message"]
        # Every line of one call repeats its input-side usage; keep the first.
        calls.setdefault(message["id"], message["usage"])
        tool_calls += sum(1 for b in message["content"] if b.get("type") == "tool_use")
    prompts = [prompt_tokens(u) for u in calls.values()]
    total = sum(prompts)
    cache_read = sum(u.get("cache_read_input_tokens", 0) for u in calls.values())
    return {
        "model_calls": len(calls),
        "tool_calls": tool_calls,
        "prompt_tokens": total,
        "cache_read_tokens": cache_read,
        "cache_read_share": round(cache_read / total, 4),
        "first_prompt": prompts[0],
        "last_prompt": prompts[-1],
        "cumulative_over_first": round(total / prompts[0], 2),
    }


def main() -> None:
    numbers = measure()
    print(json.dumps(numbers, indent=2))
    if "--write" in sys.argv:
        report = json.loads(REPORT.read_text())
        report["part0"] = numbers
        REPORT.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote part0 to {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
