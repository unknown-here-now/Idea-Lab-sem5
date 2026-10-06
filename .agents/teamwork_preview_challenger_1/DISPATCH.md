## 2026-09-03T19:35:28Z
You are teamwork_preview_challenger_1.
Your working directory is:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_challenger_1`
Your role is: Adversarial Input Validation Challenger.

MANDATORY REQUIREMENT:
You MUST read the authoritative user request and acceptance criteria in:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\ORIGINAL_REQUEST.md`
before starting your work.

Also read:
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_orchestrator_1\PROJECT.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\TEST_READY.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_worker_1\handoff.md`

Objective:
Empirically verify server resilience against adversarial and hostile inputs:
1. Author and execute an adversarial test harness (e.g. in a scratch script using `starlette.testclient.TestClient(server.app)`).
2. Test cases to execute:
   - Empty CSV files (0 bytes, whitespace).
   - Malformed/corrupted files (random binary noise, broken headers, truncated rows).
   - Out-of-bounds coordinates (latitude > 90, < -90; longitude > 180, < -180).
   - Non-numeric coordinates (strings, NaNs, Inf).
   - Negative, zero, or non-numeric `num_dark_stores` (-1, 0, 'five').
   - Single-row CSV and large synthetic CSVs (e.g. 500 rows).
   - Excessively large K (e.g. K=100 on a 15-ward dataset).
3. Confirm that the server returns HTTP 400 with structured JSON and NEVER throws unhandled HTTP 500 errors.
4. Deliverables:
   - Write `challenge_report.md` and `handoff.md` in your working directory with an explicit verdict: `APPROVE` or `REJECT`.
   - Send a message to the parent orchestrator with your report and verdict.
