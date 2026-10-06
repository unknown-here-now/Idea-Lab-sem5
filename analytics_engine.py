import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# 1. Load the 79-ward Census Dataset
df = pd.read_csv("mbmc_79_wards_census.csv")

print("="*60)
print("     MIRA-BHAYANDAR URBAN SPATIAL ANALYTICS ENGINE     ")
print("="*60)

# ------------------------------------------------------------------
# MODULE 1: BLINKIT DARK STORE PLACEMENT (E-Commerce Logistics)
# ------------------------------------------------------------------
# Filter top 25% highest demand wards
demand_threshold = df['blinkit_demand_score'].quantile(0.75)
high_demand_wards = df[df['blinkit_demand_score'] >= demand_threshold]

# Perform K-Means Clustering to find 3 optimal warehouse locations
X_blinkit = high_demand_wards[['latitude', 'longitude']].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_blinkit)
blinkit_hubs = kmeans.cluster_centers_

print("\n🛒 [BLINKIT QUICK-COMMERCE RECOMMENDATION]")
print(f"Analyzed {len(high_demand_wards)} high-density demand wards.")
for i, coord in enumerate(blinkit_hubs, 1):
    print(f"  • Dark Store #{i} Target Location -> Lat: {coord[0]:.4f}, Lon: {coord[1]:.4f}")

# ------------------------------------------------------------------
# MODULE 2: EMERGENCY AMBULANCE HUB PLACEMENT (Public Healthcare)
# ------------------------------------------------------------------
# Filter vulnerable wards (High population density AND 0 hospitals)
vulnerable_wards = df[(df['hospitals_count'] == 0) & (df['pop_density_per_sq_km'] > df['pop_density_per_sq_km'].median())]

# Calculate geometric centroid (Center of Gravity)
avg_lat = vulnerable_wards['latitude'].mean()
avg_lon = vulnerable_wards['longitude'].mean()

print("\n🚑 [EMERGENCY SERVICES RECOMMENDATION]")
print(f"Identified {len(vulnerable_wards)} critical healthcare desert wards in MBMC.")
print(f"  • Optimal Emergency Ambulance Hub -> Lat: {avg_lat:.4f}, Lon: {avg_lon:.4f}")
print("="*60)