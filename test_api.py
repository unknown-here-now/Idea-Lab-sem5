"""
test_api.py — Autonomous Spatial Intelligence Platform E2E Test Suite.

Opaque-box verification of /api/optimize and /api/health endpoints using Starlette TestClient.
Covers Tiers 1-4 across Feature Coverage, Boundary/Corner Cases, Combinations, and Real-World Scenarios.
Directly runnable via:
    python test_api.py
or
    .\\.venv\\Scripts\\python.exe test_api.py
"""

import io
import math
import os
from pathlib import Path
import sys
import time
import unittest

from starlette.testclient import TestClient

# Import the FastAPI application from server.py
from server import app

BASE_DIR = Path(__file__).resolve().parent
MBMC_PATH = BASE_DIR / "mbmc_79_wards_census.csv"
BORIVALI_PATH = BASE_DIR / "borivali_census_spatial_dataset.csv"


def get_mbmc_bytes() -> bytes:
    with open(MBMC_PATH, "rb") as f:
        return f.read()


def get_borivali_bytes() -> bytes:
    with open(BORIVALI_PATH, "rb") as f:
        return f.read()


def make_csv_bytes(headers: list[str], rows: list[list]) -> bytes:
    lines = [",".join(headers)]
    for r in rows:
        lines.append(",".join(str(x) for x in r))
    return "\n".join(lines).encode("utf-8")


# Initialize TestClient with raise_server_exceptions=False so 500s result in response codes instead of uncaught runner crashes
client = TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# TIER 1: FEATURE COVERAGE (18 Tests)
# Happy path fallback, MBMC 79 wards, Borivali 15 wards, schema structure,
# data types, integer population, dynamic trace verification.
# ==============================================================================
class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage and API Contract Verification."""

    def test_tier1_01_health_check(self):
        """Verify GET /api/health responds with 200 and healthy status metadata."""
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200, f"Expected 200 from /api/health, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("timestamp", data)
        self.assertIn("system_check", data)
        self.assertTrue(isinstance(data["system_check"], dict))

    def test_tier1_02_default_dataset_fallback(self):
        """Verify POST /api/optimize without file parameter falls back to default census dataset."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200, f"Failed fallback request: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("wards", data)
        self.assertGreaterEqual(len(data["wards"]), 15, "Default dataset should load >= 15 wards")

    def test_tier1_03_mbmc_79_wards_upload(self):
        """Verify POST /api/optimize with full MBMC 79-ward census CSV returns exactly 79 wards."""
        content = get_mbmc_bytes()
        res = client.post(
            "/api/optimize",
            files={"file": ("mbmc_79_wards_census.csv", content, "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 200, f"MBMC upload failed: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(len(data["wards"]), 79, f"Expected 79 wards, got {len(data['wards'])}")

    def test_tier1_04_borivali_15_wards_upload(self):
        """Verify POST /api/optimize with Borivali 15-ward CSV returns exactly 15 wards."""
        content = get_borivali_bytes()
        res = client.post(
            "/api/optimize",
            files={"file": ("borivali_census_spatial_dataset.csv", content, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200, f"Borivali upload failed: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(len(data["wards"]), 15, f"Expected 15 wards, got {len(data['wards'])}")

    def test_tier1_05_response_top_level_schema(self):
        """Verify response contains all required top-level keys expected by frontend and PROJECT.md."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        required_keys = ["status", "metrics", "dark_stores", "emergency_hub", "agent_trace", "llm_report", "wards"]
        for k in required_keys:
            self.assertIn(k, data, f"Missing required top-level key '{k}' in response")

    def test_tier1_06_metrics_schema_and_types(self):
        """Verify 'metrics' object contains all required fields with compliant numeric types."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        metrics = res.json().get("metrics", {})

        # Coverage percentage: 0.0 to 100.0
        self.assertIn("blinkit_coverage_pct", metrics)
        self.assertTrue(isinstance(metrics["blinkit_coverage_pct"], (int, float)))
        self.assertGreaterEqual(metrics["blinkit_coverage_pct"], 0.0)
        self.assertLessEqual(metrics["blinkit_coverage_pct"], 100.0)

        # Emergency deserts count: int >= 0
        self.assertIn("emergency_deserts_count", metrics)
        self.assertTrue(isinstance(metrics["emergency_deserts_count"], int))
        self.assertGreaterEqual(metrics["emergency_deserts_count"], 0)

        # Emergency avg distance km: float >= 0.0
        self.assertIn("emergency_avg_dist_km", metrics)
        self.assertTrue(isinstance(metrics["emergency_avg_dist_km"], (int, float)))
        self.assertGreaterEqual(metrics["emergency_avg_dist_km"], 0.0)

        # Total population 2026: int > 0
        self.assertIn("total_population_2026", metrics)
        self.assertTrue(isinstance(metrics["total_population_2026"], int))
        self.assertGreater(metrics["total_population_2026"], 0)

    def test_tier1_07_dark_stores_schema_and_types(self):
        """Verify 'dark_stores' is a list of K items with 'id', 'lat', 'lon' and valid coordinate bounds."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        stores = res.json().get("dark_stores", [])
        self.assertTrue(isinstance(stores, list))
        self.assertEqual(len(stores), 3)

        for ds in stores:
            self.assertIn("id", ds)
            self.assertTrue(isinstance(ds["id"], int))
            self.assertIn("lat", ds, "Dark store item missing 'lat' key (required by Leaflet UI)")
            self.assertIn("lon", ds, "Dark store item missing 'lon' key (required by Leaflet UI)")
            self.assertTrue(isinstance(ds["lat"], (int, float)))
            self.assertTrue(isinstance(ds["lon"], (int, float)))
            self.assertGreaterEqual(ds["lat"], -90.0)
            self.assertLessEqual(ds["lat"], 90.0)
            self.assertGreaterEqual(ds["lon"], -180.0)
            self.assertLessEqual(ds["lon"], 180.0)

    def test_tier1_08_emergency_hub_schema_and_types(self):
        """Verify 'emergency_hub' is a single dict object with 'lat' and 'lon' (not a list)."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        hub = res.json().get("emergency_hub")
        self.assertTrue(isinstance(hub, dict), "'emergency_hub' must be a dict object, NOT a list")
        self.assertIn("lat", hub, "'emergency_hub' missing 'lat' key (required by Leaflet UI)")
        self.assertIn("lon", hub, "'emergency_hub' missing 'lon' key (required by Leaflet UI)")
        self.assertTrue(isinstance(hub["lat"], (int, float)))
        self.assertTrue(isinstance(hub["lon"], (int, float)))
        self.assertGreaterEqual(hub["lat"], -90.0)
        self.assertLessEqual(hub["lat"], 90.0)
        self.assertGreaterEqual(hub["lon"], -180.0)
        self.assertLessEqual(hub["lon"], 180.0)

    def test_tier1_09_wards_schema_and_coordinates(self):
        """Verify 'wards' array contains ward objects with 'latitude', 'longitude', 'ward_id', 'hospitals_count'."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        wards = res.json().get("wards", [])
        self.assertTrue(isinstance(wards, list))
        self.assertGreater(len(wards), 0)

        for w in wards:
            self.assertIn("ward_id", w)
            self.assertIn("latitude", w, "Ward item must use 'latitude' key for frontend compatibility")
            self.assertIn("longitude", w, "Ward item must use 'longitude' key for frontend compatibility")
            self.assertIn("hospitals_count", w)
            self.assertIn("blinkit_demand_score", w)
            self.assertTrue(isinstance(w["latitude"], (int, float)))
            self.assertTrue(isinstance(w["longitude"], (int, float)))
            self.assertGreaterEqual(w["latitude"], -90.0)
            self.assertLessEqual(w["latitude"], 90.0)
            self.assertGreaterEqual(w["longitude"], -180.0)
            self.assertLessEqual(w["longitude"], 180.0)

    def test_tier1_10_wards_est_population_integer_type(self):
        """Verify 'est_population_2026' in every ward is an integer (prevents JS .toLocaleString crash)."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        wards = res.json().get("wards", [])
        self.assertGreater(len(wards), 0)

        for w in wards:
            self.assertIn("est_population_2026", w)
            val = w["est_population_2026"]
            self.assertIsNotNone(val, "Ward est_population_2026 cannot be null")
            self.assertTrue(isinstance(val, int), f"Ward est_population_2026 must be int, got {type(val)}")
            self.assertGreaterEqual(val, 0)

    def test_tier1_11_llm_report_markdown_content(self):
        """Verify 'llm_report' is a non-empty markdown string containing strategic headings."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        report = res.json().get("llm_report")
        self.assertTrue(isinstance(report, str))
        self.assertGreater(len(report), 100, "llm_report should contain a substantive policy brief")
        self.assertTrue(
            "#" in report or "**" in report,
            "llm_report should be formatted in Markdown with headers or bold sections",
        )

    def test_tier1_12_agent_trace_count_and_agents(self):
        """Verify 'agent_trace' contains at least 4 entries covering Perception, Spatial, Emergency, Policy."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        trace = res.json().get("agent_trace", [])
        self.assertTrue(isinstance(trace, list))
        self.assertGreaterEqual(len(trace), 4, f"Expected at least 4 agent trace entries, got {len(trace)}")

        agent_names = [t.get("agent", "") for t in trace]
        expected_modules = ["Perception", "Spatial", "Emergency", "Policy"]
        for mod in expected_modules:
            self.assertTrue(
                any(mod.lower() in name.lower() for name in agent_names),
                f"Missing trace entry for agent module matching '{mod}'. Found: {agent_names}",
            )

    def test_tier1_13_agent_trace_schema_structure(self):
        """Verify each agent_trace entry contains agent, action, observation, status, timestamp per PROJECT.md."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        trace = res.json().get("agent_trace", [])
        self.assertGreaterEqual(len(trace), 4)

        for i, step in enumerate(trace):
            self.assertIn("agent", step, f"Trace step {i} missing 'agent'")
            self.assertIn("action", step, f"Trace step {i} missing 'action'")
            self.assertIn("observation", step, f"Trace step {i} missing 'observation'")
            self.assertIn("status", step, f"Trace step {i} missing 'status' per interface contract")
            self.assertIn("timestamp", step, f"Trace step {i} missing 'timestamp' per interface contract")
            self.assertTrue(isinstance(step["status"], str))
            self.assertTrue(isinstance(step["timestamp"], (int, float)))

    def test_tier1_14_agent_trace_dynamic_ward_count_reflection(self):
        """Verify agent_trace dynamically reflects actual ward count processed (79 for MBMC vs 15 for Borivali)."""
        # Run MBMC (79)
        res_mbmc = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res_mbmc.status_code, 200)
        trace_mbmc = res_mbmc.json()["agent_trace"]
        all_obs_mbmc = " ".join([t.get("observation", "") for t in trace_mbmc])
        self.assertTrue(
            "79" in all_obs_mbmc,
            f"Expected trace observation to dynamically reference 79 wards for MBMC. Observations: {all_obs_mbmc}",
        )

        # Run Borivali (15)
        res_borivali = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res_borivali.status_code, 200)
        trace_borivali = res_borivali.json()["agent_trace"]
        all_obs_borivali = " ".join([t.get("observation", "") for t in trace_borivali])
        self.assertTrue(
            "15" in all_obs_borivali,
            f"Expected trace observation to dynamically reference 15 wards for Borivali. Observations: {all_obs_borivali}",
        )

    def test_tier1_15_agent_trace_dynamic_timestamp_progression(self):
        """Verify agent_trace timestamps are non-decreasing floats reflecting real execution time."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        trace = res.json().get("agent_trace", [])
        self.assertGreaterEqual(len(trace), 2)

        timestamps = [t.get("timestamp", 0.0) for t in trace]
        for i in range(len(timestamps) - 1):
            self.assertGreaterEqual(
                timestamps[i + 1],
                timestamps[i],
                f"Agent trace timestamps should be non-decreasing: {timestamps}",
            )

    def test_tier1_16_spatial_dark_stores_k_parameter_4(self):
        """Verify requesting num_dark_stores=4 produces exactly 4 dark stores."""
        res = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
            data={"num_dark_stores": "4"},
        )
        self.assertEqual(res.status_code, 200)
        stores = res.json().get("dark_stores", [])
        self.assertEqual(len(stores), 4, f"Expected 4 dark stores, got {len(stores)}")

    def test_tier1_17_spatial_dark_stores_k_parameter_5(self):
        """Verify requesting num_dark_stores=5 produces exactly 5 dark stores."""
        res = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
            data={"num_dark_stores": "5"},
        )
        self.assertEqual(res.status_code, 200)
        stores = res.json().get("dark_stores", [])
        self.assertEqual(len(stores), 5, f"Expected 5 dark stores, got {len(stores)}")

    def test_tier1_18_perception_demand_and_vulnerability_scores(self):
        """Verify perception agent scores blinkit_demand_score and emergency_vulnerability_score >= 0."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        wards = res.json().get("wards", [])
        for w in wards:
            self.assertIn("blinkit_demand_score", w)
            self.assertGreaterEqual(w["blinkit_demand_score"], 0.0)
            if "emergency_vulnerability_score" in w:
                self.assertGreaterEqual(w["emergency_vulnerability_score"], 0.0)


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (18 Tests)
# Empty CSV, malformed CSV, missing coordinates, non-numeric coordinates,
# out-of-bounds coordinates, num_dark_stores <= 0, clamping, single row.
# All negative inputs must return HTTP 400 (or 422) with {"status": "error"}.
# ==============================================================================
class TestTier2BoundaryAndCornerCases(unittest.TestCase):
    """Tier 2: Boundary Value Analysis and Negative Input Validation."""

    def test_tier2_01_empty_file_upload(self):
        """Verify uploading an empty 0-byte file returns HTTP 400 with status 'error'."""
        res = client.post(
            "/api/optimize",
            files={"file": ("empty.csv", b"", "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 400, f"Expected 400 for empty file, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_tier2_02_malformed_csv_random_bytes(self):
        """Verify uploading arbitrary binary bytes returns HTTP 400 without crashing server."""
        corrupted = b"\x00\xff\xfe\x12\x34\x56\x78\x9a\xbc\xde\xf0"
        res = client.post(
            "/api/optimize",
            files={"file": ("corrupted.bin", corrupted, "application/octet-stream")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_tier2_03_malformed_csv_broken_delimiters(self):
        """Verify uploading non-tabular text returns HTTP 400 with status 'error'."""
        broken = b"<html><body>This is an HTML page, not a CSV file</body></html>"
        res = client.post(
            "/api/optimize",
            files={"file": ("broken.html", broken, "text/plain")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_tier2_04_missing_latitude_column(self):
        """Verify CSV with longitude and population but missing latitude returns HTTP 400."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "longitude", "population_2011"],
            [["W_01", 72.85, 10000], ["W_02", 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("no_lat.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_tier2_05_missing_longitude_column(self):
        """Verify CSV with latitude and population but missing longitude returns HTTP 400."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "population_2011"],
            [["W_01", 19.28, 10000], ["W_02", 19.29, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("no_lon.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_tier2_06_missing_both_coordinates(self):
        """Verify CSV with only metadata and no coordinates returns HTTP 400."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "population_2011", "area_sq_km"],
            [["W_01", 10000, 1.2], ["W_02", 12000, 1.5]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("no_coords.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_tier2_07_non_numeric_latitude(self):
        """Verify CSV with non-numeric strings in latitude returns HTTP 400."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", "INVALID_LAT", 72.85, 10000], ["W_02", "NOT_A_NUMBER", 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("bad_lat.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_08_non_numeric_longitude(self):
        """Verify CSV with non-numeric strings in longitude returns HTTP 400."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", 19.28, "CORRUPTED_LON", 10000], ["W_02", 19.29, "BAD_DATA", 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("bad_lon.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_09_latitude_out_of_bounds_high(self):
        """Verify CSV with latitude > 90.0 returns HTTP 400 with status 'error'."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", 95.5, 72.85, 10000], ["W_02", 19.28, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("high_lat.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400, f"Latitude 95.5 must return 400, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_10_latitude_out_of_bounds_low(self):
        """Verify CSV with latitude < -90.0 returns HTTP 400 with status 'error'."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", -95.5, 72.85, 10000], ["W_02", 19.28, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("low_lat.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400, f"Latitude -95.5 must return 400, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_11_longitude_out_of_bounds_high(self):
        """Verify CSV with longitude > 180.0 returns HTTP 400 with status 'error'."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", 19.28, 185.0, 10000], ["W_02", 19.29, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("high_lon.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400, f"Longitude 185.0 must return 400, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_12_longitude_out_of_bounds_low(self):
        """Verify CSV with longitude < -180.0 returns HTTP 400 with status 'error'."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", 19.28, -185.0, 10000], ["W_02", 19.29, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("low_lon.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400, f"Longitude -185.0 must return 400, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_13_zero_num_dark_stores(self):
        """Verify num_dark_stores=0 returns HTTP 400 with status 'error'."""
        res = client.post("/api/optimize", data={"num_dark_stores": "0"})
        self.assertEqual(res.status_code, 400, f"num_dark_stores=0 must return 400, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_14_negative_num_dark_stores(self):
        """Verify num_dark_stores=-5 returns HTTP 400 with status 'error'."""
        res = client.post("/api/optimize", data={"num_dark_stores": "-5"})
        self.assertEqual(res.status_code, 400, f"num_dark_stores=-5 must return 400, got {res.status_code}")
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_tier2_15_non_integer_num_dark_stores(self):
        """Verify non-integer num_dark_stores returns HTTP 400 or 422 without 500 crash."""
        res = client.post("/api/optimize", data={"num_dark_stores": "three"})
        self.assertIn(res.status_code, [400, 422], f"Expected 400 or 422 for 'three', got {res.status_code}")

    def test_tier2_16_excessive_num_dark_stores_clamped(self):
        """Verify requesting num_dark_stores=100 on a 15-ward dataset is clamped gracefully without 500 crash."""
        res = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "100"},
        )
        # Should either succeed with clamped dark stores <= 15 or reject cleanly with 400, never 500
        self.assertNotEqual(res.status_code, 500, "Server crashed with 500 on large num_dark_stores")
        if res.status_code == 200:
            stores = res.json().get("dark_stores", [])
            self.assertLessEqual(len(stores), 15, "Clamped K cannot exceed total available wards")

    def test_tier2_17_single_row_csv(self):
        """Verify single-row CSV with num_dark_stores=1 does not crash the server."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011", "area_sq_km", "hospitals_count"],
            [["Single_Ward", 19.28, 72.85, 15000, 1.0, 1]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("single.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "1"},
        )
        self.assertNotEqual(res.status_code, 500, f"Server crashed on single-row CSV: {res.text}")

    def test_tier2_18_all_zero_population_wards(self):
        """Verify dataset with 0 population does not trigger ZeroDivisionError or crash."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011", "area_sq_km", "hospitals_count"],
            [
                ["W_01", 19.28, 72.85, 0, 1.0, 0],
                ["W_02", 19.29, 72.86, 0, 1.5, 0],
                ["W_03", 19.30, 72.87, 0, 2.0, 1],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("zero_pop.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertNotEqual(res.status_code, 500, f"Zero population caused 500 crash: {res.text}")
        if res.status_code == 200:
            data = res.json()
            # Ensure JSON values are not NaN or Inf
            self.assertTrue(math.isfinite(data["metrics"]["blinkit_coverage_pct"]))


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (10 Tests)
# Pairwise K testing, column synonyms normalization, extreme healthcare
# desert distributions, minimal column configurations.
# ==============================================================================
class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """Tier 3: Combinatorial & Cross-Feature Normalization Testing."""

    def test_tier3_01_pairwise_k2_borivali(self):
        """Pairwise test: Borivali dataset with K=2 returns exactly 2 dark stores."""
        res = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["dark_stores"]), 2)

    def test_tier3_02_pairwise_k4_borivali(self):
        """Pairwise test: Borivali dataset with K=4 returns exactly 4 dark stores."""
        res = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "4"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["dark_stores"]), 4)

    def test_tier3_03_pairwise_k6_mbmc(self):
        """Pairwise test: MBMC dataset with K=6 returns exactly 6 dark stores."""
        res = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
            data={"num_dark_stores": "6"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["dark_stores"]), 6)

    def test_tier3_04_column_synonyms_lat_lon(self):
        """Verify column aliases 'lat', 'lon', 'pop', 'hospitals' are correctly recognized."""
        csv_bytes = make_csv_bytes(
            ["ward", "lat", "lon", "pop", "hospitals"],
            [
                ["A1", 19.25, 72.84, 20000, 1],
                ["A2", 19.26, 72.85, 25000, 0],
                ["A3", 19.27, 72.86, 30000, 2],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("synonyms1.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200, f"Failed with lat/lon synonyms: {res.text}")
        data = res.json()
        self.assertEqual(len(data["wards"]), 3)
        self.assertEqual(data["wards"][0]["latitude"], 19.25)
        self.assertEqual(data["wards"][0]["longitude"], 72.84)

    def test_tier3_05_column_synonyms_uppercase(self):
        """Verify case-insensitive headers like LATITUDE, LONGITUDE, POPULATION are recognized."""
        csv_bytes = make_csv_bytes(
            ["WARD_ID", "LATITUDE", "LONGITUDE", "POPULATION", "HOSPITALS_COUNT"],
            [
                ["U1", 19.21, 72.81, 15000, 0],
                ["U2", 19.22, 72.82, 18000, 1],
                ["U3", 19.23, 72.83, 22000, 0],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("upper.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200, f"Failed uppercase column test: {res.text}")
        self.assertEqual(len(res.json()["wards"]), 3)

    def test_tier3_06_column_synonyms_wgs84(self):
        """Verify GIS aliases 'wgs84_dd_n' and 'wgs84_dd_e' are mapped to latitude/longitude."""
        csv_bytes = make_csv_bytes(
            ["name", "wgs84_dd_n", "wgs84_dd_e", "persons", "clinics"],
            [
                ["G1", 19.24, 72.83, 12000, 0],
                ["G2", 19.25, 72.84, 14000, 1],
                ["G3", 19.26, 72.85, 16000, 0],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("gis.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200, f"Failed GIS column test: {res.text}")
        self.assertEqual(len(res.json()["wards"]), 3)

    def test_tier3_07_all_wards_healthcare_deserts(self):
        """Verify calculation when all wards have hospitals_count=0 (100% desert scenario)."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011", "hospitals_count"],
            [
                ["D1", 19.25, 72.84, 25000, 0],
                ["D2", 19.26, 72.85, 28000, 0],
                ["D3", 19.27, 72.86, 30000, 0],
                ["D4", 19.28, 72.87, 32000, 0],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("all_deserts.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["metrics"]["emergency_deserts_count"], 0)
        # Emergency hub must be positioned centrally near the wards
        hub = data["emergency_hub"]
        self.assertTrue(19.24 <= hub["lat"] <= 19.29)
        self.assertTrue(72.83 <= hub["lon"] <= 72.88)

    def test_tier3_08_no_wards_healthcare_deserts(self):
        """Verify fallback when every ward has hospitals_count >= 1 (0 desert scenario)."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011", "hospitals_count"],
            [
                ["H1", 19.25, 72.84, 25000, 2],
                ["H2", 19.26, 72.85, 28000, 3],
                ["H3", 19.27, 72.86, 30000, 1],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("no_deserts.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        hub = data["emergency_hub"]
        self.assertTrue(19.24 <= hub["lat"] <= 19.28)
        self.assertTrue(72.83 <= hub["lon"] <= 72.87)

    def test_tier3_09_spatially_skewed_distribution(self):
        """Verify spatial clustering handles asymmetrical outliers without crashing."""
        csv_bytes = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011", "hospitals_count"],
            [
                ["C1", 19.200, 72.800, 50000, 0],
                ["C2", 19.201, 72.801, 55000, 0],
                ["C3", 19.202, 72.802, 60000, 1],
                ["C4", 19.203, 72.803, 45000, 0],
                ["OUTLIER", 19.350, 72.900, 10000, 2],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("skewed.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["dark_stores"]), 2)

    def test_tier3_10_minimal_columns_lat_lon_only(self):
        """Verify dataset having ONLY latitude and longitude columns infers defaults successfully."""
        csv_bytes = make_csv_bytes(
            ["latitude", "longitude"],
            [
                [19.25, 72.84],
                [19.26, 72.85],
                [19.27, 72.86],
            ],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("coords_only.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 200, f"Failed coords-only test: {res.text}")
        data = res.json()
        self.assertEqual(len(data["wards"]), 3)
        self.assertGreater(data["metrics"]["total_population_2026"], 0)


# ==============================================================================
# TIER 4: REAL-WORLD SCENARIOS & STABILITY (8 Tests)
# Full MBMC, full Borivali, request isolation, sequential idempotency,
# UI payload simulation matching index.html FormData submission.
# ==============================================================================
class TestTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: End-to-End Real-World Scenarios and Idempotency."""

    def test_tier4_01_full_mbmc_production_run(self):
        """Full end-to-end production run on MBMC 79 wards dataset with K=3."""
        content = get_mbmc_bytes()
        res = client.post(
            "/api/optimize",
            files={"file": ("mbmc_79_wards_census.csv", content, "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(data["wards"]), 79)
        self.assertEqual(len(data["dark_stores"]), 3)
        self.assertGreater(data["metrics"]["total_population_2026"], 1_000_000)

        # Emergency hub within Mira-Bhayandar geographic bounding box
        hub = data["emergency_hub"]
        self.assertTrue(19.25 <= hub["lat"] <= 19.32, f"Hub lat {hub['lat']} outside MBMC bounds")
        self.assertTrue(72.81 <= hub["lon"] <= 72.89, f"Hub lon {hub['lon']} outside MBMC bounds")

    def test_tier4_02_full_borivali_production_run(self):
        """Full end-to-end production run on Borivali 15 wards dataset with K=3."""
        content = get_borivali_bytes()
        res = client.post(
            "/api/optimize",
            files={"file": ("borivali_census_spatial_dataset.csv", content, "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(data["wards"]), 15)
        self.assertEqual(len(data["dark_stores"]), 3)
        self.assertGreater(data["metrics"]["total_population_2026"], 500_000)

        # Emergency hub within Borivali geographic bounding box
        hub = data["emergency_hub"]
        self.assertTrue(19.21 <= hub["lat"] <= 19.26, f"Hub lat {hub['lat']} outside Borivali bounds")
        self.assertTrue(72.82 <= hub["lon"] <= 72.88, f"Hub lon {hub['lon']} outside Borivali bounds")

    def test_tier4_03_request_isolation_and_idempotency(self):
        """Verify two identical requests in sequence produce identical deterministic results."""
        content = get_borivali_bytes()
        res1 = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", content, "text/csv")},
            data={"num_dark_stores": "3"},
        )
        res2 = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", content, "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)

        d1 = res1.json()
        d2 = res2.json()

        self.assertEqual(d1["metrics"]["blinkit_coverage_pct"], d2["metrics"]["blinkit_coverage_pct"])
        self.assertEqual(d1["metrics"]["total_population_2026"], d2["metrics"]["total_population_2026"])
        self.assertEqual(d1["emergency_hub"], d2["emergency_hub"])
        self.assertEqual(d1["dark_stores"], d2["dark_stores"])

    def test_tier4_04_sequential_interleaved_datasets(self):
        """Verify alternating requests (MBMC -> Borivali -> MBMC -> Borivali) suffer no state bleed."""
        res_m1 = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(len(res_m1.json()["wards"]), 79)

        res_b1 = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(len(res_b1.json()["wards"]), 15)

        res_m2 = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(len(res_m2.json()["wards"]), 79)

        res_b2 = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(len(res_b2.json()["wards"]), 15)

    def test_tier4_05_ui_formdata_payload_simulation(self):
        """Simulate the exact FormData payload constructed by index.html runOptimization()."""
        # index.html lines 354-362:
        # const formData = new FormData();
        # if (fileInput.files.length > 0) formData.append('file', fileInput.files[0]);
        # formData.append('num_dark_stores', document.getElementById('kInput').value);
        res = client.post(
            "/api/optimize",
            files={"file": ("user_upload.csv", get_borivali_bytes(), "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 200)
        res_json = res.json()

        # Check frontend KPI unpack contracts (index.html:376-379)
        self.assertIn("blinkit_coverage_pct", res_json["metrics"])
        self.assertIn("emergency_deserts_count", res_json["metrics"])
        self.assertIn("emergency_avg_dist_km", res_json["metrics"])
        self.assertIn("total_population_2026", res_json["metrics"])

        # Check frontend Ward unpacking contracts (index.html:384-415)
        for w in res_json["wards"]:
            self.assertIn("latitude", w)
            self.assertIn("longitude", w)
            self.assertIn("hospitals_count", w)
            self.assertIn("est_population_2026", w)
            self.assertIn("blinkit_demand_score", w)

        # Check frontend Dark Store unpacking contracts (index.html:432-441)
        for ds in res_json["dark_stores"]:
            self.assertIn("lat", ds)
            self.assertIn("lon", ds)
            self.assertIn("id", ds)

        # Check frontend Emergency Hub unpacking contracts (index.html:448-457)
        self.assertIn("lat", res_json["emergency_hub"])
        self.assertIn("lon", res_json["emergency_hub"])

    def test_tier4_06_ui_formdata_without_file_simulation(self):
        """Simulate index.html when user clicks 'Execute Analysis' without choosing a file."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("wards", data)
        self.assertGreater(len(data["wards"]), 0)

    def test_tier4_07_rapid_sequential_burst(self):
        """Verify server responds consistently across 5 rapid sequential bursts with varied K."""
        k_values = [2, 3, 4, 3, 5]
        for k in k_values:
            res = client.post(
                "/api/optimize",
                files={"file": ("mbmc.csv", get_mbmc_bytes(), "text/csv")},
                data={"num_dark_stores": str(k)},
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(res.json()["dark_stores"]), k)

    def test_tier4_08_error_envelope_consistency(self):
        """Verify error responses conform strictly to {'status': 'error', 'message': str}."""
        # Condition 1: Empty file
        r1 = client.post(
            "/api/optimize",
            files={"file": ("empty.csv", b"", "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(r1.status_code, 400)
        d1 = r1.json()
        self.assertEqual(d1.get("status"), "error")
        self.assertTrue(isinstance(d1.get("message"), str))

        # Condition 2: Invalid negative dark store count
        r2 = client.post("/api/optimize", data={"num_dark_stores": "-1"})
        self.assertEqual(r2.status_code, 400)
        d2 = r2.json()
        self.assertEqual(d2.get("status"), "error")
        self.assertTrue(isinstance(d2.get("message"), str))

        # Condition 3: Out-of-bounds latitude
        bad_lat = make_csv_bytes(
            ["ward_no", "latitude", "longitude", "population_2011"],
            [["W_01", 120.0, 72.85, 10000]],
        )
        r3 = client.post(
            "/api/optimize",
            files={"file": ("bad_lat.csv", bad_lat, "text/csv")},
            data={"num_dark_stores": "1"},
        )
        self.assertEqual(r3.status_code, 400)
        d3 = r3.json()
        self.assertEqual(d3.get("status"), "error")
        self.assertTrue(isinstance(d3.get("message"), str))


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================
if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTests(loader.loadTestsFromTestCase(TestTier1FeatureCoverage))
    suite.addTests(loader.loadTestsFromTestCase(TestTier2BoundaryAndCornerCases))
    suite.addTests(loader.loadTestsFromTestCase(TestTier3CrossFeatureCombinations))
    suite.addTests(loader.loadTestsFromTestCase(TestTier4RealWorldScenarios))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Total Tests Executed: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Return exit code 0 if all tests pass, exit code 1 if any fail
    sys.exit(0 if result.wasSuccessful() else 1)
