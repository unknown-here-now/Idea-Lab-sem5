# Original User Request

## Initial Request — 2026-09-03T19:04:00Z

Build a fully functional backend for the Spatial Agent platform where autonomous agents actually execute the spatial analysis (perception, clustering, dispatch, and policy synthesis) instead of using simulated traces. The system should integrate perfectly with the existing frontend UI.
Working directory: c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb
Integrity mode: development

## Requirements

### R1. Multi-Agent Backend Architecture
Implement a robust multi-agent architecture to handle the `/api/optimize` endpoint. Distinct agent modules (e.g., Perception, Spatial Optimization, Emergency Dispatch, Policy Synthesis) must process the data and pass results between each other dynamically, replacing the current simulated/hardcoded logic. The team may decide the best framework or architecture to achieve this.

### R2. Seamless UI Integration
The new backend must perfectly integrate with the existing `index.html` frontend. It must accept the same `FormData` payload (CSV file and `num_dark_stores`) and return the exact JSON schema currently expected by the frontend (`metrics`, `dark_stores`, `emergency_hub`, `agent_trace`, `llm_report`, `wards`).

### R3. Production-Grade Reliability
The system must be built to a production-grade standard. This includes strict input validation for the CSV datasets, robust error handling to prevent server crashes on malformed data, and modular code design that supports future scaling.

## Acceptance Criteria

### API Contract & Verification
- [ ] A programmatic test script (e.g., `test_api.py`) successfully posts a sample CSV to `/api/optimize` and verifies the response schema matches requirements.
- [ ] The JSON response's `agent_trace` array reflects real execution steps from the agents rather than hardcoded mock strings.
- [ ] Sending a malformed CSV or missing parameters returns a proper 400-level error JSON without crashing the server.
- [ ] Running `index.html` against the new backend functions perfectly in the browser with zero console errors.
