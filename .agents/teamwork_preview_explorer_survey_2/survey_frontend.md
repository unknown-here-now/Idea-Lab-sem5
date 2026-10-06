# Frontend Integration & UI Contract Survey Report

**Author**: Explorer Survey Agent 2 (`teamwork_preview_explorer_survey_2`)  
**Role**: Frontend Integration & UI Contract Explorer  
**Authority**: `ORIGINAL_REQUEST.md`  
**Target Codebase**: `index.html`, `server.py`, and related frontend assets  
**Date**: 2026-09-04  

---

## Executive Summary

The frontend application is a single-page geospatial dashboard contained entirely within `index.html` (542 lines). It uses Tailwind CSS (via CDN), Leaflet 1.9.4, Lucide Icons, Marked.js, and vanilla ES6 JavaScript. The dashboard communicates with the backend via a single HTTP POST endpoint: `/api/optimize`.

The backend response contract requires strict adherence: any missing keys, null values, or renamed coordinates will trigger immediate JavaScript exceptions (`TypeError`, `Invalid LatLng`), halting DOM and map rendering. Furthermore, while `index.html` does not directly bind DOM elements to `agent_trace`, this field is an explicit requirement of `ORIGINAL_REQUEST.md` (R1, R2, and acceptance criteria) and is validated by programmatic testing suites.

---

## 1. Frontend Interaction with `/api/optimize`

### 1.1 Trigger & Lifecycle
The optimization workflow is initiated when the user clicks the "Execute Analysis" button inside the left drawer:
- **HTML Element**: `<button onclick="runOptimization()" class="...">` (`index.html:225-227`)
- **Execution Function**: `async function runOptimization()` (`index.html:350-483`)

### 1.2 Step-by-Step Call Lifecycle
1. **Layer Reset**: `layersGroup.clearLayers()` clears all previous Leaflet markers, circles, and tooltips from the map.
2. **Button State to Loading**:
   - Saves original button HTML.
   - Sets button inner HTML to `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Analyzing...`.
   - Calls `lucide.createIcons()` to render the SVG spinner.
3. **FormData Construction**:
   - Instantiates `new FormData()`.
   - Inspects `#csvFile` input. If a file is selected (`fileInput.files.length > 0`), appends the file object.
   - Appends `num_dark_stores` from `#kInput` slider value.
4. **Network Request**:
   - Executes: `const response = await fetch('/api/optimize', { method: 'POST', body: formData });`
   - Parses response: `const res = await response.json();`
5. **Status Verification**:
   - Checks: `if (res.status !== 'success')`
   - If not `'success'`: displays `alert('Analysis Error: ' + res.message);`, restores button state, and returns.
6. **Data Binding & Map Rendering**:
   - Updates Executive Strip KPI cards (`#kpiCoverage`, `#kpiDeserts`, `#kpiDistance`, `#kpiPop`).
   - Iterates `res.wards` to create `L.circleMarker` objects and bind HTML tooltips.
   - Iterates `res.dark_stores` to create 2200m buffer circles (`L.circle`) and store markers (`L.marker`).
   - Renders `res.emergency_hub` with 3500m buffer circle (`L.circle`) and dispatch station marker.
   - Auto-fits map viewport to bounding box: `map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 })`.
7. **Policy Memo Rendering**:
   - Parses Markdown string `res.llm_report` via `marked.parse(res.llm_report)` into `#policyBrief`.
   - Automatically opens right drawer if closed: `if (!rightDrawerOpen) toggleRightDrawer();`.
8. **Completion / Error Handling**:
   - `catch (err)`: captures network/runtime errors and triggers `alert('Connection Error: ' + err.message);`.
   - `finally`: always restores original button text and re-runs `lucide.createIcons()`.

---

## 2. Exact FormData Parameters Sent

The frontend builds `FormData` using two parameters only:

| Parameter Key | Data Type | Requirement | Value Source & Description | Example Value |
|---|---|---|---|---|
| `file` | `File` / `Blob` | **Optional** | `<input type="file" id="csvFile" accept=".csv">`. Appended **only** if `fileInput.files.length > 0`. If no file is chosen, the key is omitted entirely from FormData. | `mbmc_79_wards_census.csv` (multipart file) |
| `num_dark_stores` | `string` (representing integer) | **Mandatory** | `<input type="range" id="kInput" min="2" max="6" value="3">`. Sent as a string representation of an integer between 2 and 6. | `"3"` |

### Backend Compatibility Note
- If `file` is omitted from FormData, the backend must gracefully fall back to the default municipality dataset (`mbmc_79_wards_census.csv` or `borivali_census_spatial_dataset.csv`).
- `num_dark_stores` arrives as form data (`FastAPI Form(3)`). The backend must cast it to `int`.

---

## 3. Exact JSON Response Schema

### 3.1 Top-Level Response Structure
When successful (`HTTP 200`):
```json
{
  "status": "success",
  "metrics": { ... },
  "wards": [ ... ],
  "dark_stores": [ ... ],
  "emergency_hub": { ... },
  "agent_trace": [ ... ],
  "llm_report": "..."
}
```

When an error occurs (`HTTP 400` / `422`):
```json
{
  "status": "error",
  "message": "Human-readable error explanation string"
}
```

---

### 3.2 Field-by-Field Schema Specification

#### A. `status`
- **Type**: `string`
- **Allowed Values**: `"success" | "error"`
- **Frontend Usage**: `if (res.status !== 'success')` triggers error dialog.

#### B. `metrics` (Object)
The `metrics` object populates the top floating Executive KPI strip:

| Key | Data Type | Units / Range | Frontend Target DOM | Render Expression | Example |
|---|---|---|---|---|---|
| `blinkit_coverage_pct` | `number` (float or int) | Percentage (`0.0` – `100.0`) | `#kpiCoverage` | `res.metrics.blinkit_coverage_pct + '%'` | `93.8` (renders `93.8%`) |
| `emergency_deserts_count` | `integer` | Count (`>= 0`) | `#kpiDeserts` | `res.metrics.emergency_deserts_count` | `14` |
| `emergency_avg_dist_km` | `number` (float) | Kilometers | `#kpiDistance` | `res.metrics.emergency_avg_dist_km` (static "km" in DOM) | `1.8` |
| `total_population_2026` | `number` (integer) | Population count | `#kpiPop` | `(res.metrics.total_population_2026 / 1000).toFixed(1) + 'k'` | `1148213` (renders `1148.2k`) |
| `total_wards` *(optional for UI, required for memo)* | `integer` | Count | Used in LLM memo synthesis | Backend report reference | `79` |
| `blinkit_wards_covered` *(optional for UI, required for memo)* | `integer` | Count | Used in LLM memo synthesis | Backend report reference | `74` |

*Critical Constraint*: `total_population_2026` **must be a valid number**. If `null` or `undefined`, `(undefined / 1000).toFixed(1)` displays `"NaNk"`.

---

#### C. `wards` (Array of Objects)
Represents the municipal ward census points for geospatial mapping:
- **Format**: Flat JSON array of objects (NOT GeoJSON FeatureCollection).
- **Target Visualization**: `L.circleMarker([w.latitude, w.longitude])` added to `layersGroup`.

Each object `w` in `res.wards` requires:

| Key | Data Type | Units / Range | Description & Frontend Logic |
|---|---|---|---|
| `ward_id` | `string` or `number` | Identifier | Displayed in tooltip header: `<span class="font-semibold ...">${w.ward_id}</span>` (e.g. `"Ward_01"`). |
| `latitude` | `number` (float) | Degrees N | **Coordinate**. Used in `L.circleMarker([w.latitude, w.longitude])` and `bounds.extend([w.latitude, w.longitude])`. |
| `longitude` | `number` (float) | Degrees E | **Coordinate**. Used in marker position and bounds extension. |
| `hospitals_count` | `number` (integer) | Count (`>= 0`) | **Classification rule**: `const isDesert = w.hospitals_count === 0;`. If 0, badge is "DESERT", marker color `#f43f5e`, radius 4.5. If >0, badge is "STANDARD", marker color `#71717a`, radius 3.5. Also rendered in tooltip: `${w.hospitals_count}`. |
| `est_population_2026` | `number` (integer) | Population count | Rendered in tooltip: `${w.est_population_2026.toLocaleString()}`. **FATAL CRASH RISK**: If `null` or `undefined`, calling `.toLocaleString()` throws an uncaught `TypeError` and crashes the entire UI! |
| `blinkit_demand_score` | `number` (float) | Score (e.g. `0.0` – `20.0`) | Rendered in tooltip: `${w.blinkit_demand_score}`. |
| `population` *(backend pass-through)* | `number` (integer) | Baseline census pop | Kept for data completeness (e.g. `10500`). |
| `emergency_vulnerability_score` *(backend pass-through)* | `number` (float) | Vulnerability index | Kept for analytics completeness (e.g. `12.5`). |

---

#### D. `dark_stores` (Array of Objects)
Represents the optimized commercial quick-commerce micro-fulfillment centers (K-Means centroids):
- **Target Visualization**:
  - Buffer circle: `L.circle([h.lat, h.lon], { radius: 2200, dashArray: '4, 4', ... })` (2.2 km catchment radius).
  - Hub marker: `L.marker([h.lat, h.lon], { icon: createIcon(groceryIconSvg, '#e4e4e7', '#a1a1aa') })`.
  - Tooltip: `Fulfillment Hub #${h.id}`.

Each object `h` in `res.dark_stores` requires:

| Key | Data Type | Description |
|---|---|---|
| `id` | `integer` or `string` | Hub sequence identifier (`1, 2, ...`). Rendered in tooltip: `Fulfillment Hub #${h.id}`. |
| `lat` | `number` (float) | Latitude of fulfillment center. |
| `lon` | `number` (float) | Longitude of fulfillment center. |

*Critical Coordinate Asymmetry Alert*: Notice the keys are **`lat`** and **`lon`** (NOT `latitude` and `longitude`).

---

#### E. `emergency_hub` (Single Object)
Represents the municipal paramedic / ambulance dispatch hub:
- **Format**: **Single Object** `{ lat, lon }` (NOT an array).
- **Target Visualization**:
  - Buffer circle: `L.circle([em.lat, em.lon], { radius: 3500, dashArray: '4, 4', ... })` (3.5 km emergency reach radius).
  - Dispatch marker: `L.marker([em.lat, em.lon], { icon: createIcon(medicalIconSvg, '#f43f5e', '#fda4af') })`.
  - Tooltip: `Emergency Dispatch Station` (styled with `.text-hazard`).

Object properties:

| Key | Data Type | Description |
|---|---|---|
| `lat` | `number` (float) | Latitude of emergency ambulance station centroid. |
| `lon` | `number` (float) | Longitude of emergency ambulance station centroid. |

*Critical Coordinate Asymmetry Alert*: Keys are **`lat`** and **`lon`**. If passed as an array or if keys are named `latitude`/`longitude`, `em.lat` is `undefined`, causing `L.circle` to throw `Error: Invalid LatLng object: (NaN, NaN)`.

---

#### F. `llm_report` (String)
Represents the executive policy brief:
- **Type**: `string` (Markdown text).
- **Frontend Target DOM**: `#policyBrief` container inside `#rightDrawer`.
- **Render Logic**:
  ```javascript
  const policyBriefContainer = document.getElementById('policyBrief');
  if (typeof marked !== 'undefined') {
      policyBriefContainer.innerHTML = marked.parse(res.llm_report);
  } else {
      policyBriefContainer.innerText = res.llm_report;
  }
  if (!rightDrawerOpen) toggleRightDrawer();
  ```
- **Clipboard Integration**: `copyMemo()` reads `#policyBrief.innerText` and copies it to `navigator.clipboard`.
- **Content Expectation**: Markdown containing executive headings (`#`, `##`, `###`), bold metrics, bullet points, and coordinate summaries.

---

#### G. `agent_trace` (Array of Objects)
- **Role**: Required by `ORIGINAL_REQUEST.md` (R1, R2, acceptance criteria: *"The JSON response's `agent_trace` array reflects real execution steps from the agents rather than hardcoded mock strings"*).
- **Legacy Schema in `server.py`**:
  ```json
  [
    {
      "agent": "Perception Agent",
      "action": "Data Sanitization & Spatial Feature Indexing",
      "observation": "Normalized 79 nodes. Extracted spatial bounds..."
    }
  ]
  ```
- **Recommended Enhanced Schema** (satisfies all test criteria and future UI inspectors):
  ```typescript
  interface AgentTraceStep {
    agent: string;          // e.g. "Perception Agent"
    action: string;         // e.g. "Spatial Data Sanitization & Feature Indexing"
    observation: string;    // e.g. "Normalized 79 wards. Identified 14 healthcare deserts."
    status?: string;        // e.g. "completed" | "success"
    timestamp?: number;     // e.g. 1725400000.123 (epoch timestamp)
    details?: any;          // optional auxiliary payload or metrics
  }
  ```

---

### 3.3 TypeScript Contract Specification

```typescript
export interface OptimizeRequestFormData {
  file?: File;              // Optional CSV file
  num_dark_stores: string;  // Integer string e.g. "3" (range: "2" to "6")
}

export interface WardRecord {
  ward_id: string | number;
  latitude: number;
  longitude: number;
  hospitals_count: number;
  est_population_2026: number;
  blinkit_demand_score: number;
  population?: number;
  emergency_vulnerability_score?: number;
}

export interface DarkStoreHub {
  id: number | string;
  lat: number;
  lon: number;
}

export interface EmergencyHub {
  lat: number;
  lon: number;
}

export interface ExecutiveMetrics {
  blinkit_coverage_pct: number;
  emergency_deserts_count: number;
  emergency_avg_dist_km: number;
  total_population_2026: number;
  total_wards?: number;
  blinkit_wards_covered?: number;
}

export interface AgentTraceStep {
  agent: string;
  action: string;
  observation: string;
  status?: string;
  timestamp?: number;
  details?: Record<string, any>;
}

export interface OptimizeSuccessResponse {
  status: "success";
  metrics: ExecutiveMetrics;
  wards: WardRecord[];
  dark_stores: DarkStoreHub[];
  emergency_hub: EmergencyHub;
  agent_trace: AgentTraceStep[];
  llm_report: string;
}

export interface OptimizeErrorResponse {
  status: "error";
  message: string;
}

export type OptimizeResponse = OptimizeSuccessResponse | OptimizeErrorResponse;
```

---

## 4. Frontend Rendering Logic & UI Components

### 4.1 Executive Strip KPI Cards
Located at top center (`absolute top-6 left-1/2 -translate-x-1/2 z-[1000] max-w-5xl`):
1. **Quick-Commerce Coverage**:
   - Element: `<span id="kpiCoverage">--%</span>`
   - Bound to: `res.metrics.blinkit_coverage_pct + '%'`
2. **Healthcare Deserts**:
   - Element: `<span id="kpiDeserts">--</span>`
   - Bound to: `res.metrics.emergency_deserts_count`
3. **Avg Response Distance**:
   - Element: `<span id="kpiDistance">--</span>` + static `<span ...>km</span>`
   - Bound to: `res.metrics.emergency_avg_dist_km`
4. **Target Demo Population**:
   - Element: `<span id="kpiPop">--</span>`
   - Bound to: `(res.metrics.total_population_2026 / 1000).toFixed(1) + 'k'`

### 4.2 Leaflet Interactive Map
- Map initialized at `[19.2830, 72.8580]`, zoom `12` using Esri Dark Gray Base tiles.
- `layersGroup = L.layerGroup().addTo(map)`.
- **Wards Layer**:
  - Evaluates `isDesert = w.hospitals_count === 0`.
  - Desert Wards: fillColor `#f43f5e`, stroke `#fda4af`, radius 4.5, weight 1, fillOpacity 1.0.
  - Standard Wards: fillColor `#71717a`, stroke `#a1a1aa`, radius 3.5, weight 0.5, fillOpacity 0.6.
  - Custom HTML Tooltip: displays Ward ID, badge (Desert/Standard), 2026 population, hospital count, and demand index.
- **Dark Stores Layer**:
  - Centered at `[h.lat, h.lon]`.
  - Draw 2200m buffer circle: `#a1a1aa`, fillOpacity 0.05, dashArray `'4, 4'`.
  - Custom icon: 28x28px rounded divIcon with zinc/gray background and grocery cart SVG.
  - Tooltip: `Fulfillment Hub #${h.id}`.
- **Emergency Hub Layer**:
  - Centered at `[em.lat, em.lon]`.
  - Draw 3500m buffer circle: `#f43f5e`, fillOpacity 0.08, dashArray `'4, 4'`.
  - Custom icon: 28x28px rounded divIcon with hazard-red background and white medical cross SVG.
  - Tooltip: `Emergency Dispatch Station`.
- **Auto-Fit Viewport**:
  - Calls `map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 })` if `res.wards.length > 0`.

### 4.3 Policy Briefing Memo Drawer
- Located in `#rightDrawer` (`w-96 glass-panel`).
- Rendered into `#policyBrief` via `marked.parse(res.llm_report)`.
- Automatically opens if closed (`rightDrawer.classList.remove('translate-x-[110%]')`).
- Copy memo button reads `#policyBrief.innerText`, copies to clipboard, and toggles Lucide check icon for 2 seconds.

---

## 5. Failure Modes & Breakage Conditions Matrix

| # | Vulnerability / Failure Mode | Root Cause in Frontend | Consequence | Backend Prevention Requirement |
|---|---|---|---|---|
| 1 | **`est_population_2026` is null/undefined** | Line 412: `${w.est_population_2026.toLocaleString()}` | **Fatal JavaScript TypeError**: `Cannot read properties of undefined (reading 'toLocaleString')`. Halts wards iteration; map rendering breaks completely. | Backend must ensure `est_population_2026` is always an integer (or fallback to `0`). |
| 2 | **`total_population_2026` is non-numeric** | Line 379: `(res.metrics.total_population_2026 / 1000).toFixed(1)` | Displays `"NaNk"` or throws `TypeError` if `res.metrics` is undefined. | Backend must strictly type `total_population_2026` as `int` or `float`. |
| 3 | **Coordinate naming mismatch in `wards`** | Lines 390, 392: `w.latitude`, `w.longitude` | Leaflet receives `[undefined, undefined]`; throws `Invalid LatLng object: (NaN, NaN)`. | Must strictly output `latitude` and `longitude` in `wards`. |
| 4 | **Coordinate naming mismatch in `dark_stores` or `emergency_hub`** | Lines 432, 448: `h.lat`, `h.lon`, `em.lat`, `em.lon` | Leaflet receives `[undefined, undefined]`; throws `Invalid LatLng object: (NaN, NaN)`. | Must strictly output `lat` and `lon` for hubs. |
| 5 | **`emergency_hub` sent as an Array** | Line 447: `const em = res.emergency_hub; em.lat` | If `res.emergency_hub` is `[{ lat, lon }]`, `em.lat` is undefined, throwing LatLng error. | `emergency_hub` must be an **Object**, not an array. |
| 6 | **Missing or null `dark_stores` / `wards` array** | Lines 384, 431: `res.wards.forEach`, `res.dark_stores.forEach` | `TypeError: Cannot read properties of undefined (reading 'forEach')`. | Backend must always return arrays (at least `[]`). |
| 7 | **FastAPI default 422/400 validation error** | Line 368: `if (res.status !== 'success') alert('Analysis Error: ' + res.message)` | FastAPI's default error returns `{"detail": [...]}` without `status` or `message`. Alert displays `"Analysis Error: undefined"`. | Backend custom exception handlers must return `{"status": "error", "message": "..."}` with appropriate HTTP 400. |
| 8 | **Uncaught server exception (HTML 500)** | Line 366: `await response.json()` | HTML response triggers `SyntaxError: Unexpected token < in JSON at position 0`. Triggers generic alert `"Connection Error: ..."`. | Wrap backend pipeline in top-level `try/except` returning JSON 400 with `"status": "error"`. |
| 9 | **Malformed CSV upload without coordinates** | Backend parsing fails if columns are not found | If unhandled, causes 500 error. | Robust column normalization with case-insensitive and alias matching. |
| 10 | **`num_dark_stores` exceeds high-demand ward count** | Clustering `KMeans(n_clusters=k)` crashes if `k > len(data)` | Server crashes on small datasets. | Enforce `k = min(num_dark_stores, len(filtered_wards))`. |
| 11 | **`llm_report` is null, object, or undefined** | Line 469: `marked.parse(res.llm_report)` | Renders `"undefined"` or causes Marked.js parser failure. | Always provide a non-empty Markdown string. |

---

## 6. Recommendations for Backend Architecture Team

1. **Strict Coordinate Field Naming**:
   - `wards[*]` -> `"latitude"`, `"longitude"`
   - `dark_stores[*]` -> `"lat"`, `"lon"`, `"id"`
   - `emergency_hub` -> `"lat"`, `"lon"`
2. **Type Safety & Coercion**:
   - All numbers must be sanitized against NaN and Inf values before serialization to avoid JSON parsing errors in browsers.
   - Null values in numeric fields (`est_population_2026`, `hospitals_count`, `blinkit_demand_score`) must be filled with default values (`0`).
3. **Agent Trace Contract**:
   - Produce real execution steps in `agent_trace` with `{ agent, action, observation, status, timestamp }`.
   - Even though `index.html` currently focuses on map and KPI rendering, the programmatic test suite (`test_api.py`) and acceptance criteria evaluate `agent_trace`.
4. **Standardized Error Envelope**:
   - In all error scenarios (invalid CSV, missing columns, impossible parameters), return:
     `{"status": "error", "message": "<descriptive reason>"}` with status code `400`.
