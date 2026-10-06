# DISPATCH: Reviewer 2 (API Contract, UI Integration & Error Handling)

Working Directory: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_reviewer_2`
Role: teamwork_preview_reviewer
Task: Review `core/validator.py`, `server.py`, UI compatibility with `index.html`, HTTP 400 error payloads, and Leaflet coordinate naming conventions.
Authority: Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_READY.md`, and `worker_1/handoff.md`.
Deliverable: `review.md` and `handoff.md` with explicit verdict (APPROVE or REQUEST_CHANGES).


## 2026-09-03T19:35:19Z
You are teamwork_preview_reviewer_2.
Your working directory is:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_reviewer_2`
Your role is: API Contract & UI Integration Reviewer.

MANDATORY REQUIREMENT:
You MUST read the authoritative user request and acceptance criteria in:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\ORIGINAL_REQUEST.md`
before starting your work.

Also read:
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_orchestrator_1\PROJECT.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\TEST_READY.md`
- `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_worker_1\handoff.md`

Objective:
1. Execute the full test suite: run `.\.venv\Scripts\python.exe test_api.py` or `python test_api.py`.
2. Inspect `core/validator.py`, `core/spatial_math.py`, `server.py`, and `index.html`.
3. Verify:
   - Exact FormData handling (`file` optional, `num_dark_stores`).
   - Exact JSON response structure (`metrics`, `dark_stores`, `emergency_hub`, `agent_trace`, `llm_report`, `wards`).
   - Coordinate naming: `latitude`/`longitude` for `wards`; `lat`/`lon` for `dark_stores` and `emergency_hub`.
   - Integer population: `est_population_2026` is cast to integer in all ward objects to prevent `.toLocaleString()` UI crashes.
   - Structured HTTP 400 error payloads on malformed CSV or parameters.
4. Deliverables:
   - Write `review.md` and `handoff.md` in your working directory with an explicit verdict: `APPROVE` or `REQUEST_CHANGES`.
   - Send a message to the parent orchestrator with your report and verdict.
