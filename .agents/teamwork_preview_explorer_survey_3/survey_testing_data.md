# Comprehensive Survey: Data Assets, Testing, & Execution Environment

**Agent**: `teamwork_preview_explorer_survey_3`  
**Role**: Data Assets, Testing, & Execution Environment Explorer  
**Working Directory**: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.agents\teamwork_preview_explorer_survey_3`  
**Date & UTC Timestamp**: 2026-09-03T19:15:00Z (Local: 2026-09-04T00:45:00+05:30)  
**Parent Orchestrator**: `b49a68e0-8bc8-42fa-b93b-fe649e51c914`

---

## 1. Executive Summary

This survey provides an exhaustive technical audit of:
1. **Data Assets**: Full structural, semantic, and boundary analysis of sample CSV datasets (`mbmc_79_wards_census.csv` and `borivali_census_spatial_dataset.csv`).
2. **Testing Suite & Verification Status**: Analysis of the current testing posture, confirmation of the absence of `test_api.py`, and complete specification of required inputs, assertions, and execution models.
3. **Execution Environment**: Python runtime versions (Virtualenv Python 3.13.1 vs System Python 3.12.0), installed packages (FastAPI 0.141.1, Starlette 1.6.0, HTTPX 0.28.1, Pandas 3.0.5, Scikit-learn 1.9.0, Numpy 2.5.1, Pydantic 2.13.4), and runner capabilities.
4. **Input Validation & Error Edge Cases**: Concrete failure modes across malformed CSV uploads, coordinate out-of-bounds, non-numeric values, negative dark store counts, and divide-by-zero vulnerabilities.
5. **Contract Compatibility**: End-to-end alignment between API response schema and the existing `index.html` frontend.

---

## 2. Inventory and Schema of Data Assets

### 2.1 Primary Dataset: `mbmc_79_wards_census.csv`
- **Location**: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\mbmc_79_wards_census.csv`
- **Filesize**: 7,869 bytes
- **Record Count**: 79 wards (rows 2 to 80; line 1 is header)
- **Geographic Coverage**: Mira-Bhayandar Municipal Corporation (MBMC), Thane District, Maharashtra, India
  - Latitude Range: `[19.2580, 19.3067]`
  - Longitude Range: `[72.8200, 72.8820]`
- **Column Schema (13 columns)**:
  | Column Name | Data Type | Range / Sample Values | Description / Formula |
  | :--- | :--- | :--- | :--- |
  | `ward_no` | string | `Ward_01` to `Ward_79` | Municipal administrative ward identifier |
  | `zone_name` | string | 6 Zones: `Bhayandar West`, `Bhayandar East`, `Mira Road West / Uttan Coastal`, `Mira Road East (Station & Central)`, `Mira Road East (Kanakia & Peripheral)`, `Kashimira & Highway Corridor` | Macro-zone classification within MBMC |
  | `latitude` | float (4 dec) | `19.2580` – `19.3067` | WGS84 decimal latitude |
  | `longitude` | float (4 dec) | `72.8200` – `72.8820` | WGS84 decimal longitude |
  | `area_sq_km` | float (2 dec) | `0.60` – `2.50` | Ward geographic surface area in square km |
  | `population_2011` | integer | `4,500` – `22,000` | Baseline 2011 Census population |
  | `households_2011` | integer | `1,105` – `5,594` | Census household count (~4.3 persons/household) |
  | `working_pop_2011` | integer | `1,654` – `8,500+` | Formal/informal workforce (~38-39% of pop) |
  | `hospitals_count` | integer | `0`, `1`, `2` | Number of clinics/hospitals (0 indicates healthcare desert) |
  | `pop_density_per_sq_km` | float (2 dec) | `3,637.45` – `20,907.69` | `population_2011 / area_sq_km` |
  | `est_population_2026` | integer | `6,710` – `32,000+` | Projected 2026 pop: `population_2011 * (1 + 0.027)^15` |
  | `blinkit_demand_score` | float (2 dec) | `2.26` – `11.50` | `(density/1000)*0.4 + (households/1000)*0.4 + (workers/1000)*0.2` |
  | `emergency_vulnerability_score` | float (2 dec) | `1.33` – `10.45` | `(density/1000) / (hospitals_count + 1)` |

### 2.2 Secondary / Benchmark Dataset: `borivali_census_spatial_dataset.csv`
- **Location**: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\borivali_census_spatial_dataset.csv`
- **Filesize**: 1,704 bytes
- **Record Count**: 15 wards (rows 2 to 16; line 1 is header)
- **Geographic Coverage**: Borivali Ward Zone (R-Central), Mumbai Suburban District, Maharashtra, India
  - Latitude Range: `[19.2215, 19.2510]`
  - Longitude Range: `[72.8250, 72.8710]`
- **Column Schema (13 columns)**:
  | Column Name | Data Type | Range / Sample Values | Description / Key Differences vs Primary |
  | :--- | :--- | :--- | :--- |
  | `ward_no` | string | `BOR_01` to `BOR_15` | Borivali ward code |
  | `locality_name` | string | e.g. `IC Colony / Holy Cross Zone`, `Borivali West Station / SV Road`, etc. | **CRITICAL DIFFERENCE**: Column 2 is named `locality_name` (instead of `zone_name`) |
  | `latitude` | float (4 dec) | `19.2215` – `19.2510` | WGS84 decimal latitude |
  | `longitude` | float (4 dec) | `72.8250` – `72.8710` | WGS84 decimal longitude |
  | `area_sq_km` | float (1-2 dec)| `0.9` – `3.0` | Ward geographic surface area |
  | `population_2011` | integer | `29,000` – `67,000` | Higher density urban core |
  | `households_2011` | integer | `6,800` – `15,800` | Household count |
  | `working_pop_2011` | integer | `11,600` – `27,500` | Working population |
  | `hospitals_count` | integer | `0`, `1`, `2` | Local hospitals |
  | `pop_density_per_sq_km` | float (2 dec) | `9,666.67` – `68,888.89` | Significantly higher urban density |
  | `est_population_2026` | integer | `39,566` – `91,413` | Projected 2026 population |
  | `blinkit_demand_score` | float (2 dec) | `8.91` – `38.56` | Much higher quick-commerce demand baseline |
  | `emergency_vulnerability_score` | float (2 dec) | `9.67` – `41.88` | High density healthcare vulnerability |

### 2.3 Supporting Data & Map Assets
- `generate_dataset.py`: Script that synthesized `mbmc_79_wards_census.csv` using `numpy.random.seed(42)` and Mumbai demographic formulas.
- `generate_map.py` & `generate_advanced_map.py`: Standalone scripts generating Leaflet/Folium visual outputs `mira_bhayandar_interactive_map.html` and `mbmc_advanced_spatial_map.html`.
- `executive_spatial_report.md`: Static artifact showing sample memo format.
- `Sem 5 UML.mdj`: StarUML architecture diagram file.

---

## 3. Investigation of Existing Test Suite & Test Scripts

### 3.1 Workspace Test Script Audit
- A search for `*test*` across the workspace revealed **zero existing test files**.
- `test_api.py` does **not currently exist** in the repository.
- There are no test directories (`tests/`, `test/`) or configuration files (`pytest.ini`, `setup.cfg`, `tox.ini`).
- The user request in `ORIGINAL_REQUEST.md` (Acceptance Criteria line 23) specifically mandates:
  > *"A programmatic test script (e.g., test_api.py) successfully posts a sample CSV to /api/optimize and verifies the response schema matches requirements."*

### 3.2 Required Test Script Architecture (`test_api.py`)
To satisfy Acceptance Criteria without requiring external uninstalled packages, `test_api.py` must be designed as follows:
1. **Testing Engine**:
   - Can use `fastapi.testclient.TestClient` / `starlette.testclient.TestClient(app)` (which runs synchronous tests in-process using `httpx`, which is already installed).
   - Alternatively or additionally, support `httpx` or `requests` against live running instance `http://127.0.0.1:8000`.
   - Use standard library `unittest` or direct assert-based script with clean exit codes (`0` on all passed, `1` on failure).
2. **Test Cases to Implement**:
   - **TC-1: Successful Optimization (Default Dataset)**:
     - Input: POST `/api/optimize` with `num_dark_stores=3`, empty file (fallback mode).
     - Assertions: HTTP 200, `status == "success"`, verifies all top-level keys (`metrics`, `dark_stores`, `emergency_hub`, `agent_trace`, `llm_report`, `wards`).
   - **TC-2: Successful Optimization with Uploaded Primary CSV (`mbmc_79_wards_census.csv`)**:
     - Input: POST multipart form with `mbmc_79_wards_census.csv` and `num_dark_stores=4`.
     - Assertions: HTTP 200, `metrics["total_wards"] == 79`, `len(dark_stores) == 4`, `emergency_hub` coords are within MBMC bounds `[19.25, 19.31]` and `[72.82, 72.89]`.
   - **TC-3: Successful Optimization with Uploaded Secondary CSV (`borivali_census_spatial_dataset.csv`)**:
     - Input: POST multipart form with `borivali_census_spatial_dataset.csv` (contains `locality_name` instead of `zone_name`).
     - Assertions: HTTP 200, `metrics["total_wards"] == 15`, `agent_trace` correctly reflects 15 nodes.
   - **TC-4: Multi-Agent Dynamic Execution Verification**:
     - Assertions: Inspect `agent_trace`. Verify it contains at least 4 distinct agents: `Perception Agent`, `Spatial Optimization Agent`, `Emergency Dispatch Agent`, and `Policy Synthesis Agent`. Ensure observations contain dynamic metrics rather than static placeholders.
   - **TC-5: Health Check Endpoint**:
     - Input: GET `/api/health`.
     - Assertions: HTTP 200, `status == "healthy"`, verify `system_check` contains census file existence flags.
   - **TC-6: Error Handling - Empty CSV File**:
     - Input: POST `/api/optimize` with file content `b""`.
     - Assertions: HTTP 400 Bad Request, `res["status"] == "error"`, message clearly states file is empty.
   - **TC-7: Error Handling - Corrupted / Malformed CSV**:
     - Input: POST `/api/optimize` with non-CSV binary / garbage data.
     - Assertions: HTTP 400 Bad Request, `res["status"] == "error"`.
   - **TC-8: Error Handling - Missing Geospatial Columns**:
     - Input: CSV with `ward_no,population` but no `latitude`/`longitude`.
     - Assertions: HTTP 400 Bad Request, message notes missing latitude/longitude.
   - **TC-9: Error Handling - All Non-Numeric Coordinates**:
     - Input: CSV with `latitude="abc", longitude="def"`.
     - Assertions: HTTP 400 Bad Request, message notes invalid coordinate values.
   - **TC-10: Error Handling - Coordinate Out-of-Bounds**:
     - Input: CSV with `latitude=95.0` or `-100.0`.
     - Assertions: HTTP 400 Bad Request, server does not crash with math domain error.
   - **TC-11: Error Handling - Negative or Zero Dark Stores**:
     - Input: POST with `num_dark_stores=0` or `num_dark_stores=-3`.
     - Assertions: HTTP 400 Bad Request, message warns `num_dark_stores` must be positive integer >= 1.

---

## 4. Python Execution Environment Inspection

### 4.1 Python Versions
- **Project Virtual Environment (`.venv`)**:
  - Configuration path: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.venv\pyvenv.cfg`
  - Python version: **Python 3.13.1**
  - Base executable: `C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe`
  - Venv Python executable: `c:\Users\hp\Desktop\Idea Lab Farmers everything\Sem5 IdeaLb\.venv\Scripts\python.exe`
- **System Environment Python**:
  - Python version: **Python 3.12.0** (located on system PATH)

### 4.2 Installed Package Audit (`.venv\Lib\site-packages`)
Full verification of packages installed in the project virtualenv:

| Package | Version | Dist-Info Directory | Relevance to Platform |
| :--- | :--- | :--- | :--- |
| `fastapi` | **0.141.1** | `fastapi-0.141.1.dist-info` | Core REST API framework |
| `uvicorn` | **0.52.4** | `uvicorn-0.52.4.dist-info` | ASGI web server |
| `starlette` | **1.6.0** | `starlette-1.6.0.dist-info` | Underlying ASGI engine (`TestClient` provider) |
| `python-multipart` | **0.0.32** | `python_multipart-0.0.32.dist-info` | Handles `UploadFile` and `Form(...)` parsing |
| `httpx` | **0.28.1** | `httpx-0.28.1.dist-info` | Async & synchronous HTTP client for testing |
| `pandas` | **3.0.5** | `pandas-3.0.5.dist-info` | Spatial dataframes & tabular manipulation |
| `numpy` | **2.5.1** | `numpy-2.5.1.dist-info` | Numerical computing and distance calculations |
| `scikit-learn` | **1.9.0** | `scikit_learn-1.9.0.dist-info` | `KMeans` spatial clustering for dark store hubs |
| `scipy` | **1.18.0** | `scipy-1.18.0.dist-info` | Advanced scientific / spatial computing |
| `pydantic` | **2.13.4** | `pydantic-2.13.4.dist-info` | Schema definition and strict validation |
| `pydantic-core` | **2.46.4** | `pydantic_core-2.46.4.dist-info` | Core Pydantic C/Rust bindings |
| `folium` | **0.20.0** | `folium-0.20.0.dist-info` | Leaflet interactive map generation |
| `branca` | **0.8.2** | `branca-0.8.2.dist-info` | HTML/SVG markup for Leaflet |
| `google-genai` | **2.18.1** | `google_genai-2.18.1.dist-info` | Google Generative AI SDK |
| `requests` | **2.34.2** | `requests-2.34.2.dist-info` | Standard HTTP client |
| `websockets` | **16.1.1** | `websockets-16.1.1.dist-info` | WebSocket protocol support |
| `anyio` | **4.14.2** | `anyio-4.14.2.dist-info` | Asynchronous I/O wrapper |
| `jinja2` | **3.1.6** | `jinja2-3.1.6.dist-info` | Templating engine |

### 4.3 Missing Packages & Tooling Constraints
- `pytest` is **not installed** in the virtualenv.
- `pytest-asyncio` is **not installed**.
- **Conclusion for Test Runner**: Any testing script or automated CI harness must execute via standard Python `python test_api.py` using `starlette.testclient.TestClient(app)` or `unittest.TestCase`.

---

## 5. Error Handling and Malformed Input Scenarios

A thorough review of `server.py` and spatial computations identifies the following critical vulnerabilities and design gaps:

### 5.1 Analysis of Current Vulnerabilities in `server.py`

1. **Empty File Upload**:
   - *Current Code*: `df = pd.read_csv(io.BytesIO(content))`
   - *Failure*: When `content == b""`, pandas throws `pandas.errors.EmptyDataError: No columns to parse from file`. Caught by generic `except Exception as e:` returning 400 with raw internal error string.
   - *Fix*: Explicitly check `if not content or len(content.strip()) == 0:` and return clean JSON: `{"status": "error", "message": "Uploaded CSV file is empty."}`.

2. **Corrupted / Non-CSV File Content**:
   - *Current Code*: Unrestricted MIME parsing.
   - *Failure*: Binary or corrupted bytes cause `UnicodeDecodeError` or `pandas.errors.ParserError`.
   - *Fix*: Validate file extension and decode with structured try-catch, returning a clean 400.

3. **Geospatial Coordinate Out-of-Bounds**:
   - *Current Code*: Coordinates are converted via `pd.to_numeric(..., errors="coerce")`, but no bounding range checks exist.
   - *Vulnerability*:
     - If latitude is out of `[-90, 90]` (e.g. `999.0`), the Haversine function:
       $$\sin^2\left(\frac{\Delta\text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta\text{lon}}{2}\right)$$
       produces values $> 1$ or invalid radians, causing `asin(sqrt(a))` to throw `ValueError: math domain error`.
     - In the frontend Leaflet map, coordinates outside `[-90, 90]` or `[-180, 180]` cause map distortion or rendering failures.
   - *Fix*: Enforce valid ranges: `-90.0 <= latitude <= 90.0` and `-180.0 <= longitude <= 180.0`. If any coordinates violate this, return HTTP 400: `"Geospatial coordinates out of valid range (lat: [-90, 90], lon: [-180, 180])."`.

4. **Non-Numeric / Corrupted Coordinate Rows**:
   - *Current Code*: `df["latitude"] = pd.to_numeric(df[lat_col], errors="coerce")` followed by `df = df.dropna(subset=["latitude", "longitude"])`.
   - *Behavior*: If only a few rows have `"N/A"` or `"corrupt"`, they are silently dropped. If *all* rows are dropped, it raises `ValueError("All coordinate values in dataset are invalid or NaN.")`.
   - *Fix*: If invalid rows are dropped, log this in `Perception Agent`'s `agent_trace` observation so the user and system are aware of sanitization decisions.

5. **Invalid Dark Store Count (`num_dark_stores <= 0`)**:
   - *Current Code*:
     ```python
     k = min(num_dark_stores, len(high_demand))
     kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(...)
     ```
   - *Failure*: If `num_dark_stores <= 0` (e.g., `0` or `-2`), `k <= 0`. Scikit-learn raises `ValueError: n_clusters must be > 0, got 0`.
   - *Fix*: Explicit boundary validation before clustering: `if num_dark_stores < 1: raise ValueError("num_dark_stores must be at least 1")`. Recommend capping `num_dark_stores` between `1` and `20` (frontend slider allows 2 to 6).

6. **Degenerate Data Sets & Zero Division**:
   - If `area_sq_km == 0` or negative: `df["pop_density_per_sq_km"] = df["population"] / df["area_sq_km"]` produces `np.inf`. JSON encoder then raises `ValueError: Out of range float values are not JSON compliant`.
   - If `total_pop == 0`: `(covered_pop / total_pop) * 100` produces `ZeroDivisionError`.
   - If dataset has 0 high-demand rows: `len(high_demand) == 0`, leading to `k = 0` and `KMeans` failure.
   - *Fix*: Ensure `area_sq_km = max(area, 0.01)`, filter out non-positive population or provide safe default, and ensure `high_demand` is never empty by falling back to `df` if needed.

7. **Monolithic Simulated Trace vs. Real Multi-Agent Execution**:
   - *Current Code*: Lines 301–336 in `server.py` return a static mock list of 4 dictionaries under `agent_trace`.
   - *Requirement (R1 & Acceptance Criteria)*: Must be decoupled into modular agent classes (Perception, Spatial Optimization, Emergency Dispatch, Policy Synthesis) that dynamically execute, exchange state objects, and generate factual trace steps reflecting actual calculations.

---

## 6. Frontend UI Data Contract (`index.html`)

To ensure seamless integration with `index.html` (R2), the `/api/optimize` endpoint must accept and return exact structures:

### 6.1 Request Contract (FormData)
- `file`: (Optional) `UploadFile` (.csv). If absent, backend falls back to `mbmc_79_wards_census.csv` (or `borivali_census_spatial_dataset.csv`).
- `num_dark_stores`: (Integer form field, default=3, range 2–6 in UI slider).

### 6.2 Response Contract (JSON)
```json
{
  "status": "success",
  "metrics": {
    "total_wards": 79,
    "total_population_2026": 1148213,
    "blinkit_coverage_pct": 93.8,
    "blinkit_wards_covered": 74,
    "emergency_deserts_count": 18,
    "emergency_avg_dist_km": 1.80
  },
  "dark_stores": [
    { "id": 1, "lat": 19.2867, "lon": 72.8417 },
    { "id": 2, "lat": 19.2934, "lon": 72.8450 },
    { "id": 3, "lat": 19.3001, "lon": 72.8542 }
  ],
  "emergency_hub": {
    "lat": 19.2760,
    "lon": 72.8711
  },
  "agent_trace": [
    {
      "agent": "Perception Agent",
      "action": "Data Sanitization & Spatial Feature Indexing",
      "observation": "Normalized 79 nodes. Extracted spatial bounds..."
    },
    {
      "agent": "Spatial Optimization Agent",
      "action": "K-Means Dual-Space Partitioning",
      "observation": "Optimized K=3 dark store hubs..."
    },
    {
      "agent": "Emergency Dispatch Agent",
      "action": "Centroid Dispersion Allocation",
      "observation": "Positioned ambulance hub at..."
    },
    {
      "agent": "Policy Synthesis Agent",
      "action": "Deterministic Natural Language Generation",
      "observation": "Compiled executive policy brief autonomously..."
    }
  ],
  "llm_report": "### 📋 AUTONOMOUS SPATIAL REASONING MEMO\n...",
  "wards": [
    {
      "ward_id": "Ward_01",
      "latitude": 19.2867,
      "longitude": 72.8417,
      "population": 11441,
      "est_population_2026": 17061,
      "hospitals_count": 2,
      "blinkit_demand_score": 8.43,
      "emergency_vulnerability_score": 5.37
    }
  ]
}
```

### 6.3 Error Contract (JSON)
On any validation failure or malformed input:
- HTTP Status Code: `400 Bad Request` (or `422` for unparseable form parameters).
- Body:
  ```json
  {
    "status": "error",
    "message": "<Clear descriptive message of the error>"
  }
  ```
- Handled gracefully in frontend `runOptimization()`:
  ```javascript
  if (res.status !== 'success') {
      alert('Analysis Error: ' + res.message);
      btn.innerHTML = originalText;
      lucide.createIcons();
      return;
  }
  ```

---

## 7. Recommended Test Harness Architecture for Implementation Team

The implementation team should create `test_api.py` with the following structure:
1. Direct import of FastAPI application from `server.py`.
2. Initialization of `starlette.testclient.TestClient(app)`.
3. Standalone execution (`python test_api.py`) with test functions:
   - `test_default_dataset_optimization()`
   - `test_uploaded_mbmc_dataset()`
   - `test_uploaded_borivali_dataset()`
   - `test_agent_trace_is_dynamic()`
   - `test_k_parameter_variations()`
   - `test_empty_csv_error()`
   - `test_corrupted_csv_error()`
   - `test_missing_lat_lon_error()`
   - `test_invalid_coordinates_error()`
   - `test_out_of_bounds_coordinates_error()`
   - `test_negative_dark_stores_error()`
4. Beautiful terminal report showing passed/failed counts and zero external runtime dependencies.
