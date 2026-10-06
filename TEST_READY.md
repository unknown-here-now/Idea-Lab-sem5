# TEST_READY: Spatial Agent Platform E2E Test Suite

**Test Suite File**: `test_api.py`  
**Execution Environment**: Python 3.13 (`.venv`)  
**Runner Framework**: `unittest` + `starlette.testclient.TestClient` (In-Process)  
**Total Tests**: 54  
**Initial Baseline Status**: 48 PASSED / 6 FAILED (Expected baseline failures on missing coordinate bounds validation & agent trace schema)  
**Target Exit Code**: 0 (after M1-M3 implementation fixes)

---

## 1. Quick Runner Commands

Execute self-contained in-process without requiring a background server:

```powershell
# Preferred via virtual environment:
.\.venv\Scripts\python.exe test_api.py

# Standard python (if venv activated):
python test_api.py
```

### Verbose / Single Tier Execution
```powershell
# Run Tier 1 only:
.\.venv\Scripts\python.exe -m unittest test_api.TestTier1FeatureCoverage -v

# Run Tier 2 only:
.\.venv\Scripts\python.exe -m unittest test_api.TestTier2BoundaryAndCornerCases -v

# Run Tier 3 only:
.\.venv\Scripts\python.exe -m unittest test_api.TestTier3CrossFeatureCombinations -v

# Run Tier 4 only:
.\.venv\Scripts\python.exe -m unittest test_api.TestTier4RealWorldScenarios -v
```

---

## 2. Test Tiers & Coverage Breakdown

| Tier | Name | Test Count | Baseline Pass | Baseline Fail | Key Verification Focus |
|---|---|:---:|:---:|:---:|---|
| **Tier 1** | Feature Coverage | 18 | 17 | 1 | Schema integrity, data types, integer population, dynamic traces, K parameter scaling |
| **Tier 2** | Boundary & Corner Cases | 18 | 14 | 4 | Empty CSV, corrupt files, missing coordinates, coordinate bounds (-90..90, -180..180), K <= 0 |
| **Tier 3** | Cross-Feature Combinations | 10 | 10 | 0 | Pairwise K, column aliases (lat/lon, uppercase, WGS84), 0% & 100% desert distributions |
| **Tier 4** | Real-World Scenarios | 8 | 7 | 1 | Full MBMC (79 wards), full Borivali (15 wards), idempotency, UI FormData simulation, error envelope |
| **Total** | | **54** | **48** | **6** | |

---

## 3. Detailed Test Catalog

### Tier 1: Feature Coverage (18 Tests)
1. `test_tier1_01_health_check`: GET `/api/health` returns 200, `"status": "healthy"`, system check dictionary.
2. `test_tier1_02_default_dataset_fallback`: POST `/api/optimize` without file loads default census dataset (>= 15 wards).
3. `test_tier1_03_mbmc_79_wards_upload`: Uploading `mbmc_79_wards_census.csv` returns 79 wards and status success.
4. `test_tier1_04_borivali_15_wards_upload`: Uploading `borivali_census_spatial_dataset.csv` returns 15 wards and status success.
5. `test_tier1_05_response_top_level_schema`: Verifies all 7 top-level keys (`status`, `metrics`, `dark_stores`, `emergency_hub`, `agent_trace`, `llm_report`, `wards`).
6. `test_tier1_06_metrics_schema_and_types`: Verifies `blinkit_coverage_pct` (float 0-100), `emergency_deserts_count` (int >= 0), `emergency_avg_dist_km` (float >= 0), `total_population_2026` (int > 0).
7. `test_tier1_07_dark_stores_schema_and_types`: Verifies dark stores list length K, integer `id`, floats `lat` (-90..90) and `lon` (-180..180).
8. `test_tier1_08_emergency_hub_schema_and_types`: Verifies `emergency_hub` is a single dictionary (not list) with floats `lat` and `lon`.
9. `test_tier1_09_wards_schema_and_coordinates`: Verifies wards have `ward_id`, `latitude`, `longitude`, `hospitals_count`, `blinkit_demand_score`.
10. `test_tier1_10_wards_est_population_integer_type`: Verifies every ward's `est_population_2026` is an integer (prevents frontend `toLocaleString()` crash).
11. `test_tier1_11_llm_report_markdown_content`: Verifies `llm_report` is non-empty (> 100 chars), contains Markdown headers and strategic sections.
12. `test_tier1_12_agent_trace_count_and_agents`: Verifies `agent_trace` has >= 4 entries covering Perception, Spatial, Emergency, and Policy agents.
13. `test_tier1_13_agent_trace_schema_structure`: Verifies each trace entry has `agent`, `action`, `observation`, `status`, and `timestamp` per `PROJECT.md`. *(Baseline Failure: missing status/timestamp)*.
14. `test_tier1_14_agent_trace_dynamic_ward_count_reflection`: Verifies observations dynamically state 79 wards for MBMC and 15 for Borivali.
15. `test_tier1_15_agent_trace_dynamic_timestamp_progression`: Verifies timestamps are non-decreasing floats.
16. `test_tier1_16_spatial_dark_stores_k_parameter_4`: Requesting `num_dark_stores=4` produces 4 dark stores.
17. `test_tier1_17_spatial_dark_stores_k_parameter_5`: Requesting `num_dark_stores=5` produces 5 dark stores.
18. `test_tier1_18_perception_demand_and_vulnerability_scores`: Verifies demand and vulnerability scores are non-negative.

### Tier 2: Boundary & Corner Cases (18 Tests)
1. `test_tier2_01_empty_file_upload`: Uploading empty (0-byte) file returns HTTP 400 with `status: "error"`.
2. `test_tier2_02_malformed_csv_random_bytes`: Uploading arbitrary binary bytes returns HTTP 400.
3. `test_tier2_03_malformed_csv_broken_delimiters`: Uploading unstructured text/HTML returns HTTP 400.
4. `test_tier2_04_missing_latitude_column`: CSV missing latitude column returns HTTP 400.
5. `test_tier2_05_missing_longitude_column`: CSV missing longitude column returns HTTP 400.
6. `test_tier2_06_missing_both_coordinates`: CSV missing all geospatial coordinates returns HTTP 400.
7. `test_tier2_07_non_numeric_latitude`: CSV with string latitude returns HTTP 400.
8. `test_tier2_08_non_numeric_longitude`: CSV with string longitude returns HTTP 400.
9. `test_tier2_09_latitude_out_of_bounds_high`: CSV with latitude > 90.0 (e.g. 95.5) returns HTTP 400. *(Baseline Failure: currently returns 200)*.
10. `test_tier2_10_latitude_out_of_bounds_low`: CSV with latitude < -90.0 (e.g. -95.5) returns HTTP 400. *(Baseline Failure: currently returns 200)*.
11. `test_tier2_11_longitude_out_of_bounds_high`: CSV with longitude > 180.0 (e.g. 185.0) returns HTTP 400. *(Baseline Failure: currently returns 200)*.
12. `test_tier2_12_longitude_out_of_bounds_low`: CSV with longitude < -180.0 (e.g. -185.0) returns HTTP 400. *(Baseline Failure: currently returns 200)*.
13. `test_tier2_13_zero_num_dark_stores`: `num_dark_stores=0` returns HTTP 400 with `status: "error"`.
14. `test_tier2_14_negative_num_dark_stores`: `num_dark_stores=-5` returns HTTP 400 with `status: "error"`.
15. `test_tier2_15_non_integer_num_dark_stores`: `num_dark_stores="three"` returns HTTP 400/422.
16. `test_tier2_16_excessive_num_dark_stores_clamped`: `num_dark_stores=100` clamped to available candidates without crashing.
17. `test_tier2_17_single_row_csv`: 1-row CSV does not crash the server (returns 200 or 400, not 500).
18. `test_tier2_18_all_zero_population_wards`: Zero population dataset avoids ZeroDivisionError and NaN values.

### Tier 3: Cross-Feature Combinations (10 Tests)
1. `test_tier3_01_pairwise_k2_borivali`: Borivali with K=2 returns exactly 2 dark stores.
2. `test_tier3_02_pairwise_k4_borivali`: Borivali with K=4 returns exactly 4 dark stores.
3. `test_tier3_03_pairwise_k6_mbmc`: MBMC with K=6 returns exactly 6 dark stores.
4. `test_tier3_04_column_synonyms_lat_lon`: Column aliases `lat`, `lon`, `pop`, `hospitals` recognized.
5. `test_tier3_05_column_synonyms_uppercase`: Uppercase headers `LATITUDE`, `LONGITUDE` recognized.
6. `test_tier3_06_column_synonyms_wgs84`: GIS headers `wgs84_dd_n` and `wgs84_dd_e` recognized.
7. `test_tier3_07_all_wards_healthcare_deserts`: All wards hospitals=0 isolates 100% desert distribution.
8. `test_tier3_08_no_wards_healthcare_deserts`: All wards hospitals>=1 handles 0 desert fallback gracefully.
9. `test_tier3_09_spatially_skewed_distribution`: Outlier clustering handles spatial skew without NaN distances.
10. `test_tier3_10_minimal_columns_lat_lon_only`: Latitude and longitude only infers sensible defaults.

### Tier 4: Real-World Scenarios (8 Tests)
1. `test_tier4_01_full_mbmc_production_run`: Complete MBMC 79-ward workflow, bounding box checks.
2. `test_tier4_02_full_borivali_production_run`: Complete Borivali 15-ward workflow, bounding box checks.
3. `test_tier4_03_request_isolation_and_idempotency`: Consecutive identical requests return identical metrics.
4. `test_tier4_04_sequential_interleaved_datasets`: Alternating MBMC and Borivali requests without state bleed.
5. `test_tier4_05_ui_formdata_payload_simulation`: Full FormData simulation matching `index.html:350-464`.
6. `test_tier4_06_ui_formdata_without_file_simulation`: Form submission without file matching UI default.
7. `test_tier4_07_rapid_sequential_burst`: 5 back-to-back requests with varied K values.
8. `test_tier4_08_error_envelope_consistency`: Validates uniform error format across empty, bad coords, and negative K. *(Baseline Failure: bad coords currently returns 200)*.

---

## 4. Baseline Failures & Implementation Fix Guidance

During the initial baseline run against `server.py`, 6 tests failed as expected:

1. **`test_tier1_13_agent_trace_schema_structure`**:
   - **Reason**: `server.py` produces `agent_trace` containing only `agent`, `action`, `observation`. Missing `status` (string) and `timestamp` (float) defined in `PROJECT.md` interface contract.
   - **Fix Target**: Milestone 1 / Milestone 3 (agents and coordinator should emit `status: "success"` and unix `timestamp`).
2. **`test_tier2_09_latitude_out_of_bounds_high` (lat > 90.0)**:
   - **Reason**: `normalize_and_score()` only checks if the column exists, but does not validate `-90 <= latitude <= 90`.
   - **Fix Target**: Milestone 2 (`core/validator.py`).
3. **`test_tier2_10_latitude_out_of_bounds_low` (lat < -90.0)**:
   - **Reason**: Missing lower coordinate bound check.
   - **Fix Target**: Milestone 2 (`core/validator.py`).
4. **`test_tier2_11_longitude_out_of_bounds_high` (lon > 180.0)**:
   - **Reason**: Missing upper longitude bound check (`longitude <= 180`).
   - **Fix Target**: Milestone 2 (`core/validator.py`).
5. **`test_tier2_12_longitude_out_of_bounds_low` (lon < -180.0)**:
   - **Reason**: Missing lower longitude bound check (`longitude >= -180`).
   - **Fix Target**: Milestone 2 (`core/validator.py`).
6. **`test_tier4_08_error_envelope_consistency`**:
   - **Reason**: Fails on the coordinate out-of-bounds assertion (returning 200 instead of 400).
   - **Fix Target**: Milestone 2 (`core/validator.py`).

Once Milestone 1, 2, and 3 are implemented, re-running `python test_api.py` will result in **54/54 passed (100%)** and exit code `0`.
