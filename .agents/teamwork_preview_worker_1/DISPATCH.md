## 2026-09-03T19:14:36Z
You are teamwork_preview_worker_1.
Your working directory is:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_worker_1`
Your role is: Multi-Agent Backend Implementation Worker.

MANDATORY REQUIREMENT:
You MUST read the authoritative user request and acceptance criteria in:
`c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\ORIGINAL_REQUEST.md`
before starting your work.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Architecture References:
- Read `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_orchestrator_1\PROJECT.md`
- Read Explorer handoffs:
  - `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_explorer_survey_1\handoff.md`
  - `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_explorer_survey_2\handoff.md`
  - `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_explorer_survey_3\handoff.md`

Exclusive Write Ownership:
- You own: `agents/*`, `core/*`, and `server.py`.
- DO NOT modify `test_api.py` or `TEST_READY.md` (owned by the test writer).

Implementation Requirements:
1. Multi-Agent Engine in `agents/`:
   - `base.py`: `AgentContext` dataclass (shared blackboard) and `BaseAgent` abstract class with `async def execute(self, context: AgentContext) -> dict`.
   - `perception_agent.py`: Ingests normalized data, performs spatial bounds calculation, computes density & demand scores, isolates healthcare deserts (hospitals_count == 0), emits dynamic `agent_trace` step with actual execution statistics.
   - `spatial_optimization_agent.py`: Isolates high-demand nodes, clamps K <= candidate count, runs KMeans (`scikit-learn`), computes 2.2km Haversine catchment and population coverage %, emits dynamic `agent_trace` step.
   - `emergency_dispatch_agent.py`: Computes vulnerability-weighted centroid for emergency hub positioning, evaluates average transit latency distance, emits dynamic `agent_trace` step.
   - `policy_synthesis_agent.py`: Generates deterministic Markdown executive policy brief (`llm_report`) from multi-agent findings offline (with optional Gemini LLM fallback if API key is present), emits dynamic `agent_trace` step.
   - `coordinator.py`: `SpatialMultiAgentCoordinator` executes agents in sequence, updates blackboard, collates dynamic `agent_trace` array.
2. Input Validation in `core/validator.py`:
   - Validates CSV file presence and non-empty content.
   - Parses CSV and validates required columns / synonyms (lat, lon, etc.).
   - Enforces coordinate bounds: `-90.0 <= latitude <= 90.0` and `-180.0 <= longitude <= 180.0`.
   - Validates `num_dark_stores >= 1`.
   - On validation errors, raises custom `ValidationError` so caller can return HTTP 400 with `{"status": "error", "message": "<descriptive error>"}`.
3. Server Integration in `server.py`:
   - Wire `/api/optimize` endpoint to use `core.validator` and `agents.coordinator`.
   - Handle optional CSV file upload (fallback to `mbmc_79_wards_census.csv` if omitted).
   - Return exact JSON schema: `status`, `metrics`, `dark_stores` (array of `{id, lat, lon}`), `emergency_hub` (object `{lat, lon}`), `agent_trace` (array of dynamic dicts), `llm_report` (markdown string), and `wards` (array of `{ward_id, latitude, longitude, hospitals_count, est_population_2026, blinkit_demand_score}`).
   - CRITICAL: Ensure `est_population_2026` is cast to `int` in all ward objects so `w.est_population_2026.toLocaleString()` in `index.html` never crashes.
   - Return HTTP 400 on `ValidationError` with `{"status": "error", "message": ...}`.
4. Verification:
   - Run tests using `run_command` (e.g. `.\.venv\Scripts\python.exe test_api.py` if test_api.py exists, or run in-process verification).
   - Verify that all endpoints respond without crashing.
5. Deliverables:
   - Write comprehensive `handoff.md` in `.agents/teamwork_preview_worker_1/` with exact verification commands and outputs.
   - Send completion message to parent orchestrator.
