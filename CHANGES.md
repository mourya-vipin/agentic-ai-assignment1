# CHANGES.md

Three lines per assignment: what it added, what it removed, what it constrained.
Removals are logged like additions.

## Assignment 1
- **Added:** a loop (`agent/loop.py`), a model (`gemini-3.5-flash-lite` via the OpenAI-compatible backend) and three tools (`read_issue`, `search_repo`, `post_comment`); four ways of doing triage (direct, workflow, agent, hybrid), a grounded success check and a results script.
- **Removed:** nothing.
- **Constrained:** the loop by three bounds (12 steps, 80,000 tokens, 300 seconds), enforced in code outside the model; the hybrid's agent hand-off by a rule on the workflow's own answer.
