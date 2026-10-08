"""Shared helpers for the ways that call the model without tools."""

from harness.formats import LABELS, normalize_path, parse_triage_comment


def ask(ctx, step: int, system: str, user: str):
    """One model call with no tools, traced. Returns the response."""
    response = ctx.client.create(system=system, messages=[{"role": "user", "content": user}])
    ctx.trace.model_call(step, response)
    return response


def labels_text(ctx) -> str:
    return ctx.prompt("labels.md")


def parse_answer(text: str) -> tuple[str, str]:
    """Label and file from a model answer; unusable parts become 'unknown' / 'none'."""
    label, file = parse_triage_comment(text)
    return (label if label in LABELS else "unknown"), (file or "none")
