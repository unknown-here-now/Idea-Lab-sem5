## 2026-09-03T19:13:16Z
You are teamwork_preview_test_writer_1.
Your working directory is:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_test_writer_1`
Your role is: E2E Test Suite Creator.

MANDATORY REQUIREMENT:
You MUST read the authoritative user request and acceptance criteria in:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\ORIGINAL_REQUEST.md`
before starting work.

Also read:
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_orchestrator_1\PROJECT.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_orchestrator_1\TEST_INFRA.md`
- Explorer handoffs in `.agents/teamwork_preview_explorer_survey_1/handoff.md`, `survey_2/handoff.md`, `survey_3/handoff.md`.

Objective:
Design and implement the comprehensive opaque-box E2E test suite in `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\test_api.py` covering Tiers 1-4:
1. Use `starlette.testclient.TestClient` on `server.py` `app` so tests run self-contained via `python test_api.py` without requiring an external server process.
2. Implement >=50 test cases organized into:
   - Tier 1: Feature Coverage (happy path fallback, mbmc 79 wards, borivali 15 wards, schema structure, data types, integer population, dynamic non-mock agent_trace validation).
   - Tier 2: Boundary & Corner Cases (empty CSV, malformed CSV, missing coordinates, non-numeric coordinates, out-of-bounds coordinates, num_dark_stores <= 0, num_dark_stores > ward count, etc. all returning HTTP 400).
   - Tier 3: Cross-Feature Combinations (pairwise tests with varying K, column synonyms, healthcare desert distributions).
   - Tier 4: Real-World Scenarios (full MBMC, full Borivali, request isolation/idempotency, UI payload simulation).
3. Ensure `test_api.py` can be executed directly via command `python test_api.py` or `.\.venv\Scripts\python.exe test_api.py` and returns exit code 0 if all tests pass, exit code 1 if any fail.
4. Run `test_api.py` using `run_command` to establish baseline results against the current server (documenting expected initial failures on validation and dynamic traces).
5. Create `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\TEST_READY.md` summarizing runner commands, test counts per tier, and coverage checklist.
6. Write `handoff.md` in your working directory and notify the parent orchestrator with your report paths.
