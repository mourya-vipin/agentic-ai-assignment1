"""Assignment 1, Part B: the grounded success check, used for every way.

Success is read from the tracker, never from anything the agent said: a run passes
when exactly one comment carries its run_id on its issue, and that comment's label
and file both match the known answer.
"""

from harness.formats import normalize_path, parse_triage_comment


def check(tracker, run_id: str, issue_number: int, answer: dict) -> bool:
    comments = tracker.comments(run_id=run_id, issue=issue_number)
    if len(comments) != 1:
        return False
    label, file = parse_triage_comment(comments[0]["body"])
    return label == str(answer["label"]).lower() and file == normalize_path(answer["file"])
