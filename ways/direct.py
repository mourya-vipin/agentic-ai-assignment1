"""Way 1, the direct call. Nobody decides the next step: there is one step.

Your code reads the issue; one model call gets it plus the repository summary and
no tools; your code posts the comment.
"""

from harness.formats import format_triage_comment

from ways.common import ask, labels_text, parse_answer


def run(ctx) -> None:
    issue = ctx.call_tool(0, "read_issue", {"number": ctx.issue_number})
    system = ctx.prompt("direct.md").replace("{labels}", labels_text(ctx)).replace("{summary}", ctx.repo_summary)
    response = ask(ctx, 1, system, issue.content)
    label, file = parse_answer(response.text)
    ctx.call_tool(1, "post_comment", {"number": ctx.issue_number, "body": format_triage_comment(label, file)})
