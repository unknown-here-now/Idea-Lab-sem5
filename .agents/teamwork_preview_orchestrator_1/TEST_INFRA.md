# E2E Test Infra: Spatial Agent Platform Backend

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.
- Test runner: Python script `test_api.py` utilizing `starlette.testclient.TestClient` against FastAPI `app` in `server.py`.
- Execution command: `python test_api.py` (or `.\.venv\Scripts\python.exe test_api.py`).

## Feature Inventory
| # | Feature | Source | Tier 1 | Tier 2 | Tier 3 |
|---|---------|--------|:------:|:------:|:------:|
| 1 | Input Validation & Error Handling | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 2 | Autonomous Perception Agent | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 3 | Spatial Optimization (K-Means) | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 4 | Emergency Dispatch Hub | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 5 | Policy Synthesis Engine | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 6 | Agent Trace Dynamic Generation | ORIGINAL_REQUEST §AC | 5 | 5 | ✓ |
| 7 | UI Contract & Schema Conformance | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |

## Test Architecture
- Test runner: `test_api.py` at workspace root.
- Uses `starlette.testclient.TestClient(app)` to send multipart/form-data POST requests to `/api/optimize`.
- Assertions check HTTP status codes (200 for valid, 400 for invalid), JSON structure, schema data types, mathematical validity (lat/lon bounds, coverage 0-100%, positive populations), and dynamic `agent_trace` contents.

## Test Tiers
1. **Tier 1: Feature Coverage (>=5 per feature, >=35 tests)**:
   - Happy path with default CSV.
   - Happy path with `mbmc_79_wards_census.csv`.
   - Happy path with `borivali_census_spatial_dataset.csv`.
   - Verification of `metrics` keys and types.
   - Verification of `dark_stores` array and coordinate objects (`lat`, `lon`).
   - Verification of `emergency_hub` object (`lat`, `lon`).
   - Verification of `wards` array and coordinate objects (`latitude`, `longitude`, integer `est_population_2026`).
   - Verification of non-empty `llm_report` markdown string.
   - Verification of dynamic `agent_trace` having >=4 real agent steps (Perception, Spatial Optimization, Emergency Dispatch, Policy Synthesis).

2. **Tier 2: Boundary & Corner Cases (>=5 per feature, >=35 tests)**:
   - Empty CSV file upload -> 400 Bad Request.
   - Malformed CSV (unparseable binary/garbage text) -> 400 Bad Request.
   - CSV missing latitude / longitude columns -> 400 Bad Request.
   - Non-numeric coordinates in CSV -> 400 Bad Request.
   - Out-of-bounds latitude (>90 or <-90) -> 400 Bad Request.
   - Out-of-bounds longitude (>180 or <-180) -> 400 Bad Request.
   - Negative or zero `num_dark_stores` (`num_dark_stores=0`, `-5`) -> 400 Bad Request.
   - Very high `num_dark_stores` (`num_dark_stores=100` exceeding ward count) -> clamped gracefully to available candidates without crashing.
   - Single-row CSV -> handled gracefully or 400.
   - All-zero population/demand CSV -> handled gracefully without division-by-zero.

3. **Tier 3: Cross-Feature Combinations (Pairwise coverage)**:
   - Custom CSV + varied K values (K=2, 3, 4, 5, 6).
   - Custom CSV with column synonyms (e.g. `locality_name` vs `zone_name`, `Lat` vs `latitude`).
   - Emergency dispatch hub calculation with asymmetric healthcare desert distribution.
   - Large population density vs low density spatial dispersion.

4. **Tier 4: Real-World Application Scenarios (>=5 tests)**:
   - Full Mira-Bhayandar Municipal Corporation (MBMC 79 wards) complete workflow.
   - Full Borivali Census (15 wards) complete workflow.
   - Rapid emergency response scenario with extreme healthcare desert clusters.
   - Multi-tenant / repeated sequential request stability (zero state leakage between requests).
   - Complete end-to-end UI simulated payload simulation matching `index.html` `FormData` submission.

## Coverage Thresholds
- Total tests: >= 50 tests in `test_api.py`.
- Pass requirement: 100% exit code 0.
