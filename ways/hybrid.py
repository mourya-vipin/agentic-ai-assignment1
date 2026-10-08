"""Way 4 (Part D), the hybrid: the workflow, handing the issue to the agent only when a
rule says the workflow is likely to be wrong. Exactly one comment is posted per run.

The rule uses only what the workflow can see while it runs: a bug or feature answer
(or an unparseable one) whose file is not under src/. Real fixes live in src/; a
choice of a doc, a changelog or no file for a bug or feature is a sign the searches
found text about the problem instead of the code with the problem.
"""

from ways import agent, workflow


def should_hand_off(label: str, file: str) -> bool:
    return label not in ("question", "docs") and not file.startswith("src/")


def run(ctx) -> None:
    label, file = workflow.decide(ctx, workflow.gather(ctx))
    if should_hand_off(label, file):
        agent.run(ctx)          # the agent posts the comment and its loop ends the run
    else:
        workflow.post(ctx, label, file)
