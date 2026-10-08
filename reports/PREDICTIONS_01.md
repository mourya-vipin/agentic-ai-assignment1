# Predictions for Assignment 1 (written before any evaluation run)

Model: gemini-3.5-flash-lite, settings fixed. Each way: 60 runs (6 issues x 10). Predictions are made after
seeing one run of each way on the two dev issues only (all three posted a comment; the agent finished in 4 to 5 steps).

| Way | Expected passes of 60 | Hardest issue | Reasoning |
|---|---|---|---|
| Direct call | 30 | 4206 | It only sees a fixed repo summary, so it cannot check what the code does; 4206 names one file in its title, and the model will likely trust the title instead of the file that actually causes the bug. |
| Workflow | 36 | 4206 | Searches find real code, but the search terms come from one fixed extraction call, so a term the model did not think of is never searched; 4206 will fail because the issue's own words point at the wrong file. |
| Agent | 42 | 4203 | It can adapt its searches after each result, so it should beat the workflow on issues whose cause is not named in the issue (4203, 4204); 4203 describes a symptom (Windows, row 1) with no code vocabulary, so it is the one most likely to be searched in circles. |

Overall: I expect agent > workflow > direct on success, and the reverse order on cost, and I expect no way to pass 4206 reliably.
