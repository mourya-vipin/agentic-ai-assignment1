"""Way 2, the workflow. Your code decides every step, in advance, in this order:

    read_issue  ->  one call to extract search terms  ->  search_repo
                ->  one call to choose the label and the file  ->  post_comment

A fixed sequence, no loop: the model never chooses a tool. Split in two halves so
Part D's hybrid can run the first, look at what it found, then decide.
"""

from harness.formats import format_triage_comment

from ways.common import ask, labels_text, parse_answer

MAX_TERMS = 4


def gather(ctx) -> dict:
    """read_issue, extract terms, search_repo for each term. Returns what was found."""
    issue = ctx.call_tool(0, "read_issue", {"number": ctx.issue_number}).content
    response = ask(ctx, 1, ctx.prompt("extract_terms.md"), issue)
    terms = []
    for line in response.text.splitlines():
        term = line.strip().strip("`'\"-* ").strip()
        if term and term.lower() not in (t.lower() for t in terms):
            terms.append(term)
    searches = [(t, ctx.call_tool(1, "search_repo", {"query": t, "max_results": 10}).content)
                for t in terms[:MAX_TERMS]]
    return {"issue": issue, "terms": terms[:MAX_TERMS], "searches": searches}


def decide(ctx, found: dict) -> tuple[str, str]:
    """One call to choose label and file from the search results. Returns (label, file)."""
    results = "\n\n".join(f"search: {t}\n{r}" for t, r in found["searches"]) or "(no searches)"
    system = ctx.prompt("choose.md").replace("{labels}", labels_text(ctx))
    response = ask(ctx, 2, system, f"{found['issue']}\n\n--- search results ---\n{results}")
    return parse_answer(response.text)


def post(ctx, label: str, file: str) -> None:
    ctx.call_tool(2, "post_comment", {"number": ctx.issue_number, "body": format_triage_comment(label, file)})


def run(ctx) -> None:
    label, file = decide(ctx, gather(ctx))
    post(ctx, label, file)
