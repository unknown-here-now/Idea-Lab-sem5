import numpy as np
import pandas as pd

# Set seed for exact mathematical consistency
np.random.seed(42)

# Mira-Bhayandar's 6 Major Administrative Zones across its 79 Census Wards
zones = [
    ("Bhayandar West", 19.2950, 72.8500, 1, 20),
    ("Bhayandar East", 19.3000, 72.8650, 21, 35),
    ("Mira Road West / Uttan Coastal", 19.2800, 72.8200, 36, 45),
    ("Mira Road East (Station & Central)", 19.2830, 72.8580, 46, 60),
    ("Mira Road East (Kanakia & Peripheral)", 19.2720, 72.8750, 61, 72),
    ("Kashimira & Highway Corridor", 19.2580, 72.8820, 73, 79),
]

wards = []

for zone_name, center_lat, center_lon, start_w, end_w in zones:
    for w in range(start_w, end_w + 1):
        # Realistic population distribution per ward (Census 2011 baseline)
        pop_2011 = int(np.random.normal(10200, 2500))
        pop_2011 = max(4500, min(pop_2011, 22000))

        # Working population (~39%) & Households (~4.3 members/household)
        workers = int(pop_2011 * np.random.uniform(0.35, 0.43))
        households = int(pop_2011 / np.random.uniform(4.0, 4.6))

        # Coordinates with realistic spatial spread
        lat = round(center_lat + np.random.uniform(-0.012, 0.012), 4)
        lon = round(center_lon + np.random.uniform(-0.012, 0.012), 4)
        area = round(np.random.uniform(0.6, 2.5), 2)

        # Hospital count (0 indicates emergency vulnerability zones)
        hospitals = (
            0
            if w
            in [
                5,
                12,
                18,
                48,
                51,
                52,
                53,
                55,
                58,
                62,
                64,
                65,
                66,
                68,
                70,
                74,
                77,
            ]
            else np.random.choice([1, 2], p=[0.7, 0.3])
        )

        wards.append(
            {
                "ward_no": f"Ward_{w:02d}",
                "zone_name": zone_name,
                "latitude": lat,
                "longitude": lon,
                "area_sq_km": area,
                "population_2011": pop_2011,
                "households_2011": households,
                "working_pop_2011": workers,
                "hospitals_count": hospitals,
            }
        )

df = pd.DataFrame(wards)

# Calculate Census & Spatial Analytics Metrics
df["pop_density_per_sq_km"] = (
    df["population_2011"] / df["area_sq_km"]
).round(2)

# Projected 2026 Population (Thane District CAGR ~2.7% growth)
df["est_population_2026"] = (df["population_2011"] * ((1 + 0.027) ** 15)).astype(
    int
)

# 1. Blinkit / Dark Store Demand Index (Density + Households + Working Pop)
df["blinkit_demand_score"] = (
    (df["pop_density_per_sq_km"] / 1000) * 0.4
    + (df["households_2011"] / 1000) * 0.4
    + (df["working_pop_2011"] / 1000) * 0.2
).round(2)

# 2. Emergency Health Vulnerability Index (High Density + 0 Hospitals)
df["emergency_vulnerability_score"] = (
    (df["pop_density_per_sq_km"] / 1000) / (df["hospitals_count"] + 1)
).round(2)

# Save file directly to your project directory
df.to_csv("mbmc_79_wards_census.csv", index=False)
print("SUCCESS: 'mbmc_79_wards_census.csv' has been created with 79 wards!")