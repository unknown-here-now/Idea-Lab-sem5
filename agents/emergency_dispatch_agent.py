"""Autonomous Emergency Dispatch Agent for healthcare desert triage and ambulance hub positioning."""

from typing import Any, Dict
import numpy as np

from agents.base import AgentContext, BaseAgent
from core.spatial_math import haversine
from core.validator import ValidationError


class EmergencyDispatchAgent(BaseAgent):
    """Positions emergency medical hub using vulnerability-weighted spatial centroid and computes transit latency."""

    def __init__(self, name: str = "Emergency Dispatch Agent"):
        super().__init__(name=name)

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        df = context.normalized_df
        if df is None or df.empty:
            raise ValidationError("EmergencyDispatchAgent received empty normalized_df in context.")

        # Isolate critical healthcare deserts with above-median density
        median_density = df["pop_density_per_sq_km"].median()
        vuln = df[(df["hospitals_count"] == 0) & (df["pop_density_per_sq_km"] >= median_density)]

        # Fallbacks if no wards meet both criteria
        if vuln.empty:
            vuln = df[df["hospitals_count"] == 0]
        if vuln.empty:
            vuln = df

        # Compute vulnerability-weighted spatial centroid
        weights = vuln["emergency_vulnerability_score"]
        total_weight = float(weights.sum())

        if total_weight > 0 and not np.isnan(total_weight):
            em_lat = round(float(np.average(vuln["latitude"], weights=weights)), 4)
            em_lon = round(float(np.average(vuln["longitude"], weights=weights)), 4)
        else:
            em_lat = round(float(vuln["latitude"].mean()), 4)
            em_lon = round(float(vuln["longitude"].mean()), 4)

        emergency_hub = {"lat": em_lat, "lon": em_lon}
        context.emergency_hub = emergency_hub

        # Transit latency to vulnerable wards
        vuln_dists = [
            haversine(r["latitude"], r["longitude"], em_lat, em_lon)
            for _, r in vuln.iterrows()
        ]
        avg_em_dist = round(float(np.mean(vuln_dists)), 2) if vuln_dists else 0.0
        max_em_dist = round(float(np.max(vuln_dists)), 2) if vuln_dists else 0.0

        context.metrics.update({
            "emergency_deserts_count": len(vuln),
            "emergency_avg_dist_km": avg_em_dist,
            "emergency_max_dist_km": max_em_dist,
        })

        action_name = "Centroid Dispersion Allocation"
        observation_text = (
            f"Positioned ambulance hub at ({em_lat:.4f}, {em_lon:.4f}) via vulnerability-weighted centroid across "
            f"{len(vuln)} critical healthcare desert nodes, achieving {avg_em_dist} km average transit latency "
            f"(maximum transit radius: {max_em_dist} km)."
        )

        trace_entry = context.add_trace(
            agent=self.name,
            action=action_name,
            observation=observation_text,
            status="completed",
        )

        return {
            "emergency_hub": emergency_hub,
            "vulnerable_nodes_count": len(vuln),
            "avg_transit_dist_km": avg_em_dist,
            "max_transit_dist_km": max_em_dist,
            "trace": trace_entry,
        }
