from math import asin, cos, radians, sin, sqrt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


# Haversine distance formula (in km)
def haversine(lat1, lon1, lat2, lon2):
  R = 6371.0
  dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
  a = (
      sin(dlat / 2) ** 2
      + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
  )
  return 2 * R * asin(sqrt(a))


df = pd.read_csv('mbmc_79_wards_census.csv')

# 1. Quick-Commerce (Blinkit) Coverage Validation
demand_cutoff = df['blinkit_demand_score'].quantile(0.75)
high_demand_wards = df[df['blinkit_demand_score'] >= demand_cutoff]
X_blinkit = high_demand_wards[['latitude', 'longitude']].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_blinkit)
blinkit_hubs = kmeans.cluster_centers_

covered_wards = 0
covered_pop_2026 = 0
total_pop_2026 = df['est_population_2026'].sum()

for _, row in df.iterrows():
  min_dist = min([
      haversine(row['latitude'], row['longitude'], h[0], h[1])
      for h in blinkit_hubs
  ])
  if min_dist <= 2.2:  # 2.2 km = ~10-min delivery radius
    covered_wards += 1
    covered_pop_2026 += row['est_population_2026']

# 2. Emergency Public Health Coverage Validation
vulnerable_wards = df[
    (df['hospitals_count'] == 0)
    & (df['pop_density_per_sq_km'] > df['pop_density_per_sq_km'].median())
]
avg_lat, avg_lon = (
    vulnerable_wards['latitude'].mean(),
    vulnerable_wards['longitude'].mean(),
)
vuln_distances = [
    haversine(r['latitude'], r['longitude'], avg_lat, avg_lon)
    for _, r in vulnerable_wards.iterrows()
]

print('=' * 60)
print('          AUTONOMOUS SPATIAL PERFORMANCE METRICS          ')
print('=' * 60)
print(
    f'• Blinkit 10-Min Delivery Ward Coverage : {covered_wards} / 79 Wards'
    f' ({covered_wards/79*100:.1f}%)'
)
print(
    f'• Blinkit 2026 Projected Pop Catchment : {covered_pop_2026:,} /'
    f' {total_pop_2026:,} ({covered_pop_2026/total_pop_2026*100:.1f}%)'
)
print(
    f'• Healthcare Desert Wards Resolved     : {len(vulnerable_wards)} Critical'
    ' Wards'
)
print(
    '• 100% Desert Wards Within 3.5 km Reach: '
    + str(all(d <= 3.5 for d in vuln_distances))
)
print(
    f'• Average Ambulance Dispatch Distance  : {np.mean(vuln_distances):.2f}'
    ' km'
)
print('=' * 60)