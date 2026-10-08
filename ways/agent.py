"""Way 3, the agent. The model decides, at runtime, what to call and when to stop.

Part A's loop, with all three tools. The agent posts its own comment through
post_comment; the loop writes the trace, including trace.end.
"""

from agent.loop import load_bounds, run_loop


def run(ctx) -> None:
    system = ctx.prompt("agent.md").replace("{labels}", ctx.prompt("labels.md"))
    message = f"Triage issue #{ctx.issue_number}."
    run_loop(ctx.client, ctx.tools, system, message, load_bounds(), ctx.trace)
