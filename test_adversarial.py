"""test_adversarial.py — Empirical Adversarial and Hostile Input Test Harness.

Validates server resilience against adversarial inputs:
- Empty files (0 bytes, whitespace)
- Malformed/corrupted payloads (binary noise, truncated rows, broken quotes, HTML/JSON)
- Out-of-bounds coordinates (lat > 90, < -90; lon > 180, < -180)
- Non-numeric coordinates (strings, NaNs, Infs)
- Invalid num_dark_stores (negative, zero, strings, floats)
- Single-row CSV and large synthetic CSV (500 rows)
- Excessively large K (clamping verification)
- Structural verification of HTTP 400 responses (no unhandled 500s)
"""

import io
import json
import math
import os
import random
import sys
import unittest

from starlette.testclient import TestClient

# Import app under test
from server import app

client = TestClient(app, raise_server_exceptions=False)


def make_csv(headers: list, rows: list) -> bytes:
    lines = [",".join(str(h) for h in headers)]
    for r in rows:
        lines.append(",".join(str(x) for x in r))
    return "\n".join(lines).encode("utf-8")


class AdversarialValidationTests(unittest.TestCase):
    """Adversarial stress-test suite targeting input validation and edge cases."""

    # -------------------------------------------------------------------------
    # 1. Empty CSV Files
    # -------------------------------------------------------------------------
    def test_adv_01_empty_0_byte_file(self):
        """Empty 0-byte file must return HTTP 400 with structured JSON error."""
        res = client.post(
            "/api/optimize",
            files={"file": ("empty.csv", b"", "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertTrue(bool(data.get("message")))

    def test_adv_02_whitespace_only_file(self):
        """File with only whitespace (spaces, tabs, newlines) must return HTTP 400."""
        res = client.post(
            "/api/optimize",
            files={"file": ("whitespace.csv", b"   \r\n \t \n  \n", "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertTrue(bool(data.get("message")))

    def test_adv_03_newlines_only_file(self):
        """File with multiple newlines but zero content must return HTTP 400."""
        res = client.post(
            "/api/optimize",
            files={"file": ("newlines.csv", b"\n\n\n\n\n", "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # 2. Malformed / Corrupted Files
    # -------------------------------------------------------------------------
    def test_adv_04_random_binary_noise(self):
        """Random binary payload (unprintable bytes) must return HTTP 400 without crashing."""
        noise = bytes([random.randint(0, 255) for _ in range(512)])
        res = client.post(
            "/api/optimize",
            files={"file": ("corrupt.bin", noise, "application/octet-stream")},
            data={"num_dark_stores": "3"},
        )
        self.assertNotEqual(res.status_code, 500, "Server crashed with 500 on random binary noise")
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_adv_05_null_bytes_in_file(self):
        """Payload containing null bytes must return HTTP 400."""
        null_payload = b"ward_id,latitude,longitude\x00\x00\x001,19.28,72.85\x00\x00"
        res = client.post(
            "/api/optimize",
            files={"file": ("nulls.csv", null_payload, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertNotEqual(res.status_code, 500)
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_adv_06_html_content_disguised_as_csv(self):
        """HTML body disguised as CSV must return HTTP 400."""
        html_payload = b"<!DOCTYPE html><html><head><title>404</title></head><body>Server Error</body></html>"
        res = client.post(
            "/api/optimize",
            files={"file": ("page.csv", html_payload, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    def test_adv_07_json_content_disguised_as_csv(self):
        """JSON payload disguised as CSV must return HTTP 400."""
        json_payload = b'{"error": "Invalid token", "code": 401, "records": [1, 2, 3]}'
        res = client.post(
            "/api/optimize",
            files={"file": ("data.csv", json_payload, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    def test_adv_08_truncated_rows(self):
        """CSV with ragged / truncated rows must return HTTP 400 cleanly."""
        ragged_csv = b"ward_id,latitude,longitude,population,hospitals\n1,19.28,72.85,10000,1\n2,19.29\n3,19.30,72.87,15000,0,extra1,extra2\n"
        res = client.post(
            "/api/optimize",
            files={"file": ("ragged.csv", ragged_csv, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertNotEqual(res.status_code, 500)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    def test_adv_09_unclosed_quotes(self):
        """CSV with unclosed quotes causing parser breakdown must return HTTP 400."""
        broken_quotes = b'ward_id,latitude,longitude\n"W_01,19.28,72.85\nW_02,19.29,"unclosed string'
        res = client.post(
            "/api/optimize",
            files={"file": ("quotes.csv", broken_quotes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertNotEqual(res.status_code, 500)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    # -------------------------------------------------------------------------
    # 3. Out-of-Bounds Coordinates
    # -------------------------------------------------------------------------
    def test_adv_10_latitude_extreme_high(self):
        """Latitude > 90.0 (e.g. 90.0001, 999.0) must return HTTP 400."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", 90.0001, 72.85, 10000], ["W2", 19.28, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")
        self.assertIn("Latitude", res.json().get("message", ""))

    def test_adv_11_latitude_extreme_low(self):
        """Latitude < -90.0 (e.g. -90.0001, -999.0) must return HTTP 400."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", -90.0001, 72.85, 10000], ["W2", 19.28, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")
        self.assertIn("Latitude", res.json().get("message", ""))

    def test_adv_12_longitude_extreme_high(self):
        """Longitude > 180.0 (e.g. 180.0001, 500.0) must return HTTP 400."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", 19.28, 180.0001, 10000], ["W2", 19.29, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")
        self.assertIn("Longitude", res.json().get("message", ""))

    def test_adv_13_longitude_extreme_low(self):
        """Longitude < -180.0 (e.g. -180.0001, -500.0) must return HTTP 400."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", 19.28, -180.0001, 10000], ["W2", 19.29, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")
        self.assertIn("Longitude", res.json().get("message", ""))

    # -------------------------------------------------------------------------
    # 4. Non-Numeric Coordinates (Strings, NaNs, Infs)
    # -------------------------------------------------------------------------
    def test_adv_14_non_numeric_string_coords(self):
        """String coordinate values must return HTTP 400 with structured JSON."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", "invalid_lat", "invalid_lon", 10000], ["W2", 19.28, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    def test_adv_15_nan_coordinates(self):
        """NaN coordinate values must return HTTP 400."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", "NaN", 72.85, 10000], ["W2", 19.28, 72.86, 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    def test_adv_16_infinity_coordinates(self):
        """Infinity coordinate values must return HTTP 400."""
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population"],
            [["W1", "inf", 72.85, 10000], ["W2", 19.28, "-inf", 12000]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "2"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("status"), "error")

    # -------------------------------------------------------------------------
    # 5. Invalid num_dark_stores
    # -------------------------------------------------------------------------
    def test_adv_17_num_dark_stores_negative(self):
        """Negative num_dark_stores must return HTTP 400."""
        res = client.post("/api/optimize", data={"num_dark_stores": "-1"})
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_adv_18_num_dark_stores_zero(self):
        """Zero num_dark_stores must return HTTP 400."""
        res = client.post("/api/optimize", data={"num_dark_stores": "0"})
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    def test_adv_19_num_dark_stores_word_string(self):
        """String word for num_dark_stores ('five') must return HTTP 400 or 422."""
        res = client.post("/api/optimize", data={"num_dark_stores": "five"})
        self.assertIn(res.status_code, [400, 422])
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    def test_adv_20_num_dark_stores_float_string(self):
        """Floating-point string for num_dark_stores ('3.7') must return HTTP 400 or 422."""
        res = client.post("/api/optimize", data={"num_dark_stores": "3.7"})
        self.assertIn(res.status_code, [400, 422])
        data = res.json()
        self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # 6. Single-Row and Large Synthetic CSVs
    # -------------------------------------------------------------------------
    def test_adv_21_single_row_csv_k1(self):
        """Single-row CSV with num_dark_stores=1 must succeed with valid schema and zero 500 error."""
        csv_bytes = make_csv(
            ["ward_no", "latitude", "longitude", "population_2011", "area_sq_km", "hospitals_count"],
            [["SingleWard", 19.281, 72.855, 25000, 2.0, 1]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("single.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "1"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["dark_stores"]), 1)
        self.assertEqual(len(data["wards"]), 1)
        self.assertEqual(data["metrics"]["blinkit_coverage_pct"], 100.0)

    def test_adv_22_single_row_csv_k_greater_than_1(self):
        """Single-row CSV with num_dark_stores=5 must clamp K to 1 without crashing."""
        csv_bytes = make_csv(
            ["ward_no", "latitude", "longitude", "population_2011", "area_sq_km", "hospitals_count"],
            [["SingleWard", 19.281, 72.855, 25000, 2.0, 0]],
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("single.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "5"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["dark_stores"]), 1)

    def test_adv_23_large_synthetic_csv_500_rows(self):
        """Large synthetic dataset with 500 wards must process without crash, memory leak, or 500 error."""
        rows = []
        base_lat, base_lon = 19.20, 72.80
        for i in range(500):
            lat = round(base_lat + (i % 25) * 0.01, 6)
            lon = round(base_lon + (i // 25) * 0.01, 6)
            pop = 5000 + (i * 37) % 50000
            area = round(0.5 + (i % 10) * 0.3, 2)
            hosp = 1 if (i % 3 == 0) else 0
            rows.append([f"Ward_{i+1:03d}", lat, lon, pop, area, hosp])

        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population", "area_sq_km", "hospitals_count"],
            rows,
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("synthetic_500.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "8"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["wards"]), 500)
        self.assertEqual(len(data["dark_stores"]), 8)
        self.assertTrue(data["metrics"]["total_population_2026"] > 0)
        self.assertTrue(len(data["agent_trace"]) >= 4)

    # -------------------------------------------------------------------------
    # 7. Excessively Large K Clamping
    # -------------------------------------------------------------------------
    def test_adv_24_excessive_k_clamping_borivali(self):
        """Requesting K=100 on Borivali (15 wards) must clamp K <= 15 without 500 crash."""
        borivali_path = os.path.join(os.path.dirname(__file__), "borivali_census_spatial_dataset.csv")
        with open(borivali_path, "rb") as f:
            borivali_bytes = f.read()

        res = client.post(
            "/api/optimize",
            files={"file": ("borivali.csv", borivali_bytes, "text/csv")},
            data={"num_dark_stores": "100"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        stores = data.get("dark_stores", [])
        self.assertLessEqual(len(stores), 15)
        self.assertGreaterEqual(len(stores), 1)

    def test_adv_25_excessive_k_clamping_mbmc(self):
        """Requesting K=999 on MBMC (79 wards) must clamp K <= 79 without 500 crash."""
        mbmc_path = os.path.join(os.path.dirname(__file__), "mbmc_79_wards_census.csv")
        with open(mbmc_path, "rb") as f:
            mbmc_bytes = f.read()

        res = client.post(
            "/api/optimize",
            files={"file": ("mbmc.csv", mbmc_bytes, "text/csv")},
            data={"num_dark_stores": "999"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        stores = data.get("dark_stores", [])
        self.assertLessEqual(len(stores), 79)
        self.assertGreaterEqual(len(stores), 1)

    # -------------------------------------------------------------------------
    # 8. All Points Identical (Degenerate Spatial Geometry)
    # -------------------------------------------------------------------------
    def test_adv_26_degenerate_identical_coordinates(self):
        """All wards sharing identical coordinates must not trigger KMeans crash or singular matrix."""
        rows = [
            [f"Ward_{i+1}", 19.2800, 72.8500, 10000, 1.0, 0]
            for i in range(10)
        ]
        csv_bytes = make_csv(
            ["ward_id", "latitude", "longitude", "population", "area_sq_km", "hospitals_count"],
            rows,
        )
        res = client.post(
            "/api/optimize",
            files={"file": ("identical_coords.csv", csv_bytes, "text/csv")},
            data={"num_dark_stores": "3"},
        )
        self.assertNotEqual(res.status_code, 500)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["dark_stores"]), 1)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AdversarialValidationTests)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
