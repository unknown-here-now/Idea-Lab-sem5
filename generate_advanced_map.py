import folium
from folium.plugins import HeatMap, MiniMap
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# 1. Load Census Dataset
df = pd.read_csv("mbmc_79_wards_census.csv")

# 2. Base Map with Multi-Tile Layer Support
m = folium.Map(
    location=[19.2830, 72.8580],
    zoom_start=13,
    tiles="CartoDB positron",
    name="Clean Street View",
)
folium.TileLayer("OpenStreetMap", name="Detailed Map").add_to(m)
folium.TileLayer("CartoDB dark_matter", name="Dark Mode View").add_to(m)

# 3. Create Feature Groups (Layer Controls)
fg_all_wards = folium.FeatureGroup(name="All 79 Census Wards", show=True)
fg_vulnerable = folium.FeatureGroup(
    name="🚨 Healthcare Deserts (0 Hospitals)", show=True
)
fg_blinkit = folium.FeatureGroup(
    name="🛒 Blinkit Hubs & 10-Min Delivery Radii", show=True
)
fg_emergency = folium.FeatureGroup(
    name="🚑 Ambulance Hub & Coverage Zone", show=True
)
fg_heatmap = folium.FeatureGroup(name="🔥 Demand Heatmap Layer", show=False)

# ------------------------------------------------------------------
# MODULE 1: HEATMAP LAYER
# ------------------------------------------------------------------
heat_data = [
    [row["latitude"], row["longitude"], row["blinkit_demand_score"]]
    for _, row in df.iterrows()
]
HeatMap(
    heat_data,
    radius=18,
    blur=15,
    min_opacity=0.4,
    gradient={0.2: "blue", 0.6: "lime", 1.0: "red"},
).add_to(fg_heatmap)

# ------------------------------------------------------------------
# MODULE 2: ALL WARDS & HEALTHCARE DESERTS
# ------------------------------------------------------------------
demand_cutoff = df["blinkit_demand_score"].quantile(0.75)

for _, row in df.iterrows():
    is_desert = row["hospitals_count"] == 0
    color = (
        "#e74c3c"
        if is_desert
        else (
            "#2ecc71"
            if row["blinkit_demand_score"] >= demand_cutoff
            else "#3498db"
        )
    )

    popup_html = f"""
    <div style="font-family: Arial; min-width: 180px;">
        <h4 style="margin: 0 0 5px; color: {color};">{row['ward_no']} ({row['zone_name']})</h4>
        <hr style="margin: 3px 0;">
        <b>Est. 2026 Pop:</b> {row['est_population_2026']:,}<br>
        <b>Households:</b> {row['households_2011']:,}<br>
        <b>Hospitals:</b> {row['hospitals_count']}<br>
        <b>Blinkit Demand Score:</b> {row['blinkit_demand_score']}<br>
        <b>Emergency Risk Index:</b> {row['emergency_vulnerability_score']}
    </div>
    """

    marker = folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.75,
        popup=folium.Popup(popup_html, max_width=300),
    )

    if is_desert:
        marker.add_to(fg_vulnerable)
    else:
        marker.add_to(fg_all_wards)

# ------------------------------------------------------------------
# MODULE 3: BLINKIT DARK STORES & 10-MIN CATCHMENT RADII
# ------------------------------------------------------------------
high_demand_wards = df[df["blinkit_demand_score"] >= demand_cutoff]
X_blinkit = high_demand_wards[["latitude", "longitude"]].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_blinkit)
blinkit_hubs = kmeans.cluster_centers_

for i, coord in enumerate(blinkit_hubs, 1):
    # Dark store pin
    folium.Marker(
        location=[coord[0], coord[1]],
        popup=f"<b>🛒 Blinkit Dark Store #{i}</b><br>Coordinates: {coord[0]:.4f}, {coord[1]:.4f}",
        icon=folium.Icon(color="green", icon="shopping-cart", prefix="fa"),
    ).add_to(fg_blinkit)

    # 10-Minute Delivery Catchment Zone (2.2 km radius buffer)
    folium.Circle(
        location=[coord[0], coord[1]],
        radius=2200,
        color="#27ae60",
        fill=True,
        fill_color="#2ecc71",
        fill_opacity=0.15,
        dash_array="5, 5",
        tooltip=f"Blinkit Store #{i} 10-Min Delivery Radius (2.2 km)",
    ).add_to(fg_blinkit)

# ------------------------------------------------------------------
# MODULE 4: EMERGENCY AMBULANCE HUB & COVERAGE ZONE
# ------------------------------------------------------------------
vulnerable_wards = df[
    (df["hospitals_count"] == 0)
    & (df["pop_density_per_sq_km"] > df["pop_density_per_sq_km"].median())
]
avg_lat = vulnerable_wards["latitude"].mean()
avg_lon = vulnerable_wards["longitude"].mean()

# Hub marker
folium.Marker(
    location=[avg_lat, avg_lon],
    popup=f"<b>🚑 Emergency Ambulance Hub</b><br>Target Placement: {avg_lat:.4f}, {avg_lon:.4f}",
    icon=folium.Icon(color="red", icon="plus", prefix="fa"),
).add_to(fg_emergency)

# Emergency Golden Hour Response Zone (3.5 km radius buffer)
folium.Circle(
    location=[avg_lat, avg_lon],
    radius=3500,
    color="#c0392b",
    fill=True,
    fill_color="#e74c3c",
    fill_opacity=0.12,
    dash_array="8, 8",
    tooltip="Emergency Rapid Dispatch Zone (3.5 km)",
).add_to(fg_emergency)

# ------------------------------------------------------------------
# MODULE 5: FLOATING DASHBOARD & LEGEND
# ------------------------------------------------------------------
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000; background-color: white; 
            padding: 14px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.2); font-family: Arial; font-size: 12px; width: 230px;">
    <h4 style="margin: 0 0 8px; font-size: 14px;"><b>MBMC Spatial Analytics</b></h4>
    <div style="margin-bottom: 4px;"><span style="color: #27ae60; font-size: 16px;">●</span> Blinkit Dark Store (K=3)</div>
    <div style="margin-bottom: 4px;"><span style="color: #c0392b; font-size: 16px;">●</span> Emergency Ambulance Hub</div>
    <div style="margin-bottom: 4px;"><span style="color: #e74c3c; font-size: 14px;">●</span> Healthcare Desert Ward</div>
    <div style="margin-bottom: 4px;"><span style="color: #2ecc71; font-size: 14px;">●</span> High Delivery Demand Ward</div>
    <div style="margin-bottom: 6px;"><span style="color: #3498db; font-size: 14px;">●</span> Standard Census Ward</div>
    <hr style="margin: 6px 0;">
    <small style="color: #7f8c8d;">Total Wards Analyzed: <b>79</b><br>Target City: <b>Mira-Bhayandar</b></small>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Add Layers, MiniMap, and Layer Control
fg_all_wards.add_to(m)
fg_vulnerable.add_to(m)
fg_blinkit.add_to(m)
fg_emergency.add_to(m)
fg_heatmap.add_to(m)

MiniMap(toggle_display=True, position="bottomright").add_to(m)
folium.LayerControl(position="topright", collapsed=False).add_to(m)

# Save
output_file = "mbmc_advanced_spatial_map.html"
m.save(output_file)
print(f"SUCCESS: Advanced map generated -> {output_file}")