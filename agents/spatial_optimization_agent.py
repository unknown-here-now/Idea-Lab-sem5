"""Autonomous Spatial Optimization Agent for quick-commerce dark store placement and catchment coverage."""

from typing import Any, Dict
from sklearn.cluster import KMeans

from agents.base import AgentContext, BaseAgent
from core.spatial_math import haversine
from core.validator import ValidationError


class SpatialOptimizationAgent(BaseAgent):
    """Isolates high-demand nodes, clusters spatial centroids via KMeans, and calculates 2.2km catchment coverage."""

    def __init__(self, name: str = "Spatial Optimization Agent"):
        super().__init__(name=name)

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        df = context.normalized_df
        if df is None or df.empty:
            raise ValidationError("SpatialOptimizationAgent received empty normalized_df in context.")

        # Isolate high-demand nodes (70th percentile cutoff)
        cutoff = df["blinkit_demand_score"].quantile(0.70)
        high_demand = df[df["blinkit_demand_score"] >= cutoff]
        if high_demand.empty:
            high_demand = df

        # If high-demand candidate pool has fewer nodes than requested K, expand candidates by top demand
        num_requested = context.num_dark_stores
        if len(high_demand) < num_requested and len(df) > len(high_demand):
            target_count = min(num_requested, len(df))
            high_demand = df.sort_values(by="blinkit_demand_score", ascending=False).head(target_count)

        # Dynamic K clamping: 1 <= K <= candidate count
        k = min(num_requested, len(high_demand))
        k = max(1, k)

        # Run KMeans clustering
        coords = high_demand[["latitude", "longitude"]].values
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(coords)

        dark_stores = [
            {
                "id": i + 1,
                "lat": round(float(center[0]), 4),
                "lon": round(float(center[1]), 4),
            }
            for i, center in enumerate(kmeans.cluster_centers_)
        ]
        context.dark_stores = dark_stores

        # 2.2km Haversine catchment and population coverage calculation
        total_pop = int(df["est_population_2026"].sum())
        covered_pop = 0
        covered_wards = 0

        for _, r in df.iterrows():
            min_dist = min([
                haversine(r["latitude"], r["longitude"], h["lat"], h["lon"])
                for h in dark_stores
            ])
            if min_dist <= 2.2:
                covered_wards += 1
                covered_pop += int(r["est_population_2026"])

        coverage_pct = round((covered_pop / total_pop) * 100, 1) if total_pop > 0 else 0.0

        context.metrics.update({
            "total_wards": len(df),
            "total_population_2026": total_pop,
            "blinkit_coverage_pct": coverage_pct,
            "blinkit_wards_covered": covered_wards,
        })

        action_name = "K-Means Dual-Space Partitioning"
        observation_text = (
            f"Optimized K={k} dark store hubs from {len(high_demand)} high-demand candidates "
            f"(clustering inertia: {kmeans.inertia_:.2f}). Reached {coverage_pct}% of population "
            f"({covered_pop:,}/{total_pop:,} residents in {covered_wards}/{len(df)} wards) "
            f"in sub-10 min reach (2.2 km buffer)."
        )

        trace_entry = context.add_trace(
            agent=self.name,
            action=action_name,
            observation=observation_text,
            status="completed",
        )

        return {
            "k_selected": k,
            "candidates_count": len(high_demand),
            "dark_stores": dark_stores,
            "coverage_pct": coverage_pct,
            "covered_wards": covered_wards,
            "covered_pop": covered_pop,
            "trace": trace_entry,
        }
