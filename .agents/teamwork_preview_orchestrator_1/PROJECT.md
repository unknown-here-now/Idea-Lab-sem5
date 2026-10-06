# Project: Spatial Agent Multi-Agent Platform Backend

## Architecture
- **Framework**: FastAPI (Asynchronous Web Framework) running on Uvicorn.
- **Multi-Agent Engine** (`agents/`):
  - `base.py`: `BaseAgent` abstract class and `AgentContext` shared blackboard state.
  - `perception_agent.py`: Autonomous data sanitization, spatial density calculation, feature indexing, healthcare desert isolation.
  - `spatial_optimization_agent.py`: Autonomous K-Means spatial clustering, dynamic K-clamping, catchment buffering, population coverage metrics.
  - `emergency_dispatch_agent.py`: Autonomous centroid dispersion allocation for emergency hub, transit latency matrices.
  - `policy_synthesis_agent.py`: Autonomous deterministic neuro-symbolic report generator with optional Gemini LLM fallback.
  - `coordinator.py`: `SpatialMultiAgentCoordinator` sequential pipeline execution and dynamic `agent_trace` collation.
- **Validation Engine** (`core/validator.py`):
  - Strict CSV schema validation, coordinate bounds checking (`-90 <= lat <= 90`, `-180 <= lon <= 180`), positive dark store counts (`num_dark_stores >= 1`).
  - Structured HTTP 400 error payload: `{"status": "error", "message": "<reason>"}`.
- **API Endpoint** (`server.py`):
  - `/api/optimize`: `multipart/form-data` endpoint receiving `file` (optional) and `num_dark_stores` (optional).
  - Returns exact JSON schema expected by `index.html`: `metrics`, `dark_stores`, `emergency_hub`, `agent_trace`, `llm_report`, `wards`.
- **E2E Test Suite** (`test_api.py`):
  - In-process `starlette.testclient.TestClient` runner validating API schema, dynamic traces, error handling, and data edge cases.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Strict Input Validation | Validate CSV format, headers, coordinate bounds, positive dark stores, return 400 on malformed input | M2 | ORIGINAL_REQUEST §R3, Survey 3 |
| 2 | Autonomous Perception Agent | Normalize data, calculate densities, demand score, isolate healthcare deserts, emit dynamic trace | M1 | ORIGINAL_REQUEST §R1, Survey 1 |
| 3 | Autonomous Spatial Optimization Agent | K-Means clustering, dark store placement, population reach metrics, emit dynamic trace | M1 | ORIGINAL_REQUEST §R1, Survey 1 |
| 4 | Autonomous Emergency Dispatch Agent | Centroid hub positioning, transit latency evaluation, emit dynamic trace | M1 | ORIGINAL_REQUEST §R1, Survey 1 |
| 5 | Autonomous Policy Synthesis Agent | Multi-agent consensus aggregation, deterministic markdown executive brief, emit dynamic trace | M1 | ORIGINAL_REQUEST §R1, Survey 1 |
| 6 | Agent Blackboard Coordinator | Sequential execution pipeline, shared context, dynamic agent_trace aggregation | M1 | ORIGINAL_REQUEST §R1, Survey 1 |
| 7 | UI Schema & Endpoint Integration | /api/optimize wiring, FormData unpacking, exact JSON schema with correct types (e.g. integer population) | M3 | ORIGINAL_REQUEST §R2, Survey 2 |
| 8 | Comprehensive E2E Test Suite | test_api.py validating schema, dynamic traces, 400-level error handling, edge cases | E2E Track | ORIGINAL_REQUEST Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Suite | Create test_api.py covering Tiers 1-4, schema validation, negative tests | None | PLANNED |
| M1 | Multi-Agent Core Engine | Implement agents/ package (base, perception, spatial, emergency, policy, coordinator) | None | PLANNED |
| M2 | Input Validation & Error Handling | Implement core/validator.py and error models returning structured 400 responses | None | PLANNED |
| M3 | Server Endpoint & UI Integration | Wire /api/optimize in server.py to coordinator and validator; verify exact JSON schema | M1, M2 | PLANNED |
| M4 | Final Milestone: 100% E2E Pass & Hardening | Pass all test_api.py tests (Tiers 1-4) + Tier 5 adversarial coverage hardening | E2E, M3 | PLANNED |

## Interface Contracts

### Client ↔ Server (/api/optimize)
- **Request**: POST `multipart/form-data`
  - `file`: (Optional) CSV file upload. Fallback to `mbmc_79_wards_census.csv` if missing or empty filename.
  - `num_dark_stores`: (Optional) integer string (default 3, clamped 1 <= K <= N).
- **Success Response** (HTTP 200):
  ```json
  {
    "status": "success",
    "metrics": {
      "blinkit_coverage_pct": float,
      "emergency_deserts_count": int,
      "emergency_avg_dist_km": float,
      "total_population_2026": int
    },
    "dark_stores": [
      { "id": int, "lat": float, "lon": float }
    ],
    "emergency_hub": {
      "lat": float,
      "lon": float
    },
    "agent_trace": [
      {
        "agent": str,
        "action": str,
        "observation": str,
        "status": str,
        "timestamp": float
      }
    ],
    "llm_report": str,
    "wards": [
      {
        "ward_id": str | int,
        "latitude": float,
        "longitude": float,
        "hospitals_count": int,
        "est_population_2026": int,
        "blinkit_demand_score": float
      }
    ]
  }
  ```
- **Error Response** (HTTP 400 / 422):
  ```json
  {
    "status": "error",
    "message": "Descriptive error message"
  }
  ```

### Coordinator ↔ Agents (`AgentContext`)
- `context.raw_data`: `pd.DataFrame`
- `context.normalized_df`: `pd.DataFrame`
- `context.num_dark_stores`: `int`
- `context.healthcare_deserts`: `pd.DataFrame`
- `context.dark_stores`: `list[dict]` (`id`, `lat`, `lon`, `capacity`)
- `context.emergency_hub`: `dict` (`lat`, `lon`)
- `context.metrics`: `dict` (`blinkit_coverage_pct`, `emergency_deserts_count`, `emergency_avg_dist_km`, `total_population_2026`)
- `context.agent_trace`: `list[dict]` (`agent`, `action`, `observation`, `status`, `timestamp`)
- `context.policy_report`: `str` (Markdown)

## Code Layout
- `agents/`:
  - `__init__.py`
  - `base.py`
  - `perception_agent.py`
  - `spatial_optimization_agent.py`
  - `emergency_dispatch_agent.py`
  - `policy_synthesis_agent.py`
  - `coordinator.py`
- `core/`:
  - `__init__.py`
  - `validator.py`
- `server.py`: FastAPI server entrypoint.
- `test_api.py`: Comprehensive test runner using `starlette.testclient.TestClient`.
