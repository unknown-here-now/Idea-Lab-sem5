# DISPATCH: Explorer Survey 2 (Frontend Integration & UI Contract)

Working Directory: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_explorer_survey_2`
Role: teamwork_preview_explorer
Task: UI contract survey of index.html, JS logic, FormData payload, expected JSON response schema (`metrics`, `dark_stores`, `emergency_hub`, `agent_trace`, `llm_report`, `wards`), and frontend error handling.
Authority: Read `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\ORIGINAL_REQUEST.md`.
Deliverable: `survey_frontend.md` and `handoff.md` in working directory.

## 2026-09-03T19:05:55Z
Objective:
Investigate `index.html` and any frontend JS/CSS assets in the repository:
1. How does the frontend interact with `/api/optimize`? Find the exact form submission / fetch call.
2. What exact FormData parameters are sent? (e.g. CSV file key, num_dark_stores key, any other parameters).
3. What is the EXACT JSON schema expected in the response? Detail all fields:
   - `metrics` (what keys, data types, units)
   - `dark_stores` (array format, properties: lat, lon, capacity, demand, assigned points, etc.)
   - `emergency_hub` (properties: lat, lon, coverage radius, etc.)
   - `agent_trace` (array of agent trace steps: agent name, status, action, timestamp, details)
   - `llm_report` (markdown string or object? how is it rendered?)
   - `wards` (GeoJSON or array? properties?)
4. Trace all frontend rendering logic: Leaflet map markers, charts, agent trace UI, metric cards, policy report display.
5. Identify potential console errors or rendering breakage conditions (e.g., missing keys, null values, type mismatches).

Deliverables:
1. Write detailed findings to `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_explorer_survey_2\survey_frontend.md`.
2. Write a comprehensive `handoff.md` in your working directory with full schema specification and frontend integration constraints.
3. Send a completion message to the parent orchestrator with the paths to your reports.
