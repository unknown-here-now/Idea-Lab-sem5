import folium
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# 1. Load the 79-ward Census Dataset
df = pd.read_csv("mbmc_79_wards_census.csv")

print("Generating Interactive Map for Mira-Bhayandar...")

# 2. Initialize the Map centered on Mira-Bhayandar (Lat: 19.2830, Lon: 72.8580)
mira_map = folium.Map(
    location=[19.2830, 72.8580], zoom_start=13, tiles="OpenStreetMap"
)

# ------------------------------------------------------------------
# MODULE 1: PLOT ALL 79 WARDS
# ------------------------------------------------------------------
# Red = Emergency Vulnerable (0 Hospitals)
# Green = Top 25% Blinkit Demand Wards
# Blue = Regular Wards
high_demand_cutoff = df["blinkit_demand_score"].quantile(0.75)

for _, row in df.iterrows():
    if row["hospitals_count"] == 0:
        color = "red"
        status = "Healthcare Desert (0 Hospitals)"
    elif row["blinkit_demand_score"] >= high_demand_cutoff:
        color = "green"
        status = "High Blinkit Demand"
    else:
        color = "blue"
        status = "Standard Ward"

    popup_text = f"""
    <b>{row['ward_no']} ({row['zone_name']})</b><br>
    Status: {status}<br>
    Population (2011): {row['population_2011']}<br>
    Est. Pop (2026): {row['est_population_2026']}<br>
    Hospitals: {row['hospitals_count']}<br>
    Blinkit Demand Score: {row['blinkit_demand_score']}
    """

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=250),
    ).add_to(mira_map)

# ------------------------------------------------------------------
# MODULE 2: CALCULATE & PLOT BLINKIT DARK STORES (K-Means Clustering)
# ------------------------------------------------------------------
high_demand_wards = df[df["blinkit_demand_score"] >= high_demand_cutoff]
X_blinkit = high_demand_wards[["latitude", "longitude"]].values

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_blinkit)
blinkit_hubs = kmeans.cluster_centers_

for i, coord in enumerate(blinkit_hubs, 1):
    folium.Marker(
        location=[coord[0], coord[1]],
        popup=f"<b>🛒 Blinkit Dark Store #{i}</b><br>Optimized 10-Min Delivery Hub",
        icon=folium.Icon(color="darkgreen", icon="shopping-cart"),
    ).add_to(mira_map)

# ------------------------------------------------------------------
# MODULE 3: CALCULATE & PLOT EMERGENCY AMBULANCE HUB (Centroid)
# ------------------------------------------------------------------
vulnerable_wards = df[
    (df["hospitals_count"] == 0)
    & (df["pop_density_per_sq_km"] > df["pop_density_per_sq_km"].median())
]

avg_lat = vulnerable_wards["latitude"].mean()
avg_lon = vulnerable_wards["longitude"].mean()

folium.Marker(
    location=[avg_lat, avg_lon],
    popup="<b>🚑 Emergency Ambulance Hub</b><br>Optimized Standby Station for Healthcare Deserts",
    icon=folium.Icon(color="red", icon="plus-sign"),
).add_to(mira_map)

# ------------------------------------------------------------------
# SAVE MAP TO HTML FILE
# ------------------------------------------------------------------
map_filename = "mira_bhayandar_interactive_map.html"
mira_map.save(map_filename)

print("=" * 60)
print(f"SUCCESS! Interactive map saved as '{map_filename}'.")
print("Open this HTML file in Chrome or Edge to view your map!")
print("=" * 60)