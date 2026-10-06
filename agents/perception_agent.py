"""Autonomous Perception Agent for data sanitization, spatial bounding, and healthcare desert isolation."""

from typing import Any, Dict
import numpy as np
import pandas as pd

from agents.base import AgentContext, BaseAgent
from core.validator import (
    AREA_ALIASES,
    HH_ALIASES,
    HOSP_ALIASES,
    LAT_ALIASES,
    LON_ALIASES,
    POP_ALIASES,
    WORK_ALIASES,
    ValidationError,
    validate_dataframe,
)


class PerceptionAgent(BaseAgent):
    """Ingests raw spatial data, calculates densities & demand scores, and isolates healthcare deserts."""

    def __init__(self, name: str = "Perception Agent"):
        super().__init__(name=name)

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        raw_df = context.raw_data if context.raw_data is not None else context.normalized_df
        if raw_df is None or raw_df.empty:
            raise ValidationError("PerceptionAgent received empty or missing dataset in context.")

        # Ensure schema and coordinates are valid
        df = validate_dataframe(raw_df)

        cols = {str(c).lower().strip(): c for c in df.columns}

        pop_col = next((cols[k] for k in POP_ALIASES if k in cols), None)
        area_col = next((cols[k] for k in AREA_ALIASES if k in cols), None)
        hh_col = next((cols[k] for k in HH_ALIASES if k in cols), None)
        work_col = next((cols[k] for k in WORK_ALIASES if k in cols), None)
        hosp_col = next((cols[k] for k in HOSP_ALIASES if k in cols), None)

        # Populate features with safe fallbacks
        df["population"] = (
            pd.to_numeric(df[pop_col], errors="coerce").fillna(10000)
            if pop_col
            else 10000
        )
        # Avoid division by zero in area
        area_series = pd.to_numeric(df[area_col], errors="coerce").fillna(1.5) if area_col else pd.Series(1.5, index=df.index)
        df["area_sq_km"] = area_series.clip(lower=0.01)

        df["households"] = (
            pd.to_numeric(df[hh_col], errors="coerce").fillna(df["population"] / 4.3)
            if hh_col
            else df["population"] / 4.3
        )
        df["working_pop"] = (
            pd.to_numeric(df[work_col], errors="coerce").fillna(df["population"] * 0.38)
            if work_col
            else df["population"] * 0.38
        )
        df["hospitals_count"] = (
            pd.to_numeric(df[hosp_col], errors="coerce").fillna(0).astype(int)
            if hosp_col
            else 0
        )

        # Ward identification aliases
        WARD_ALIASES = [
            "ward_no",
            "ward_id",
            "ward",
            "ward_name",
            "locality_name",
            "name",
            "zone_name",
        ]
        ward_col = next((cols[k] for k in WARD_ALIASES if k in cols), None)
        if ward_col:
            df["ward_id"] = df[ward_col].astype(str)
        else:
            df["ward_id"] = [f"Ward_{i+1:02d}" for i in range(len(df))]

        # Densities and growth projections
        df["pop_density_per_sq_km"] = (df["population"] / df["area_sq_km"]).round(2)
        
        # 2026 projected population with 2.7% annual growth compound (15 years)
        projected_pop = (df["population"] * ((1 + 0.027) ** 15)).round().astype(int)
        df["est_population_2026"] = projected_pop

        # Blinkit quick-commerce demand index
        df["blinkit_demand_score"] = (
            (df["pop_density_per_sq_km"] / 1000.0) * 0.4
            + (df["households"] / 1000.0) * 0.4
            + (df["working_pop"] / 1000.0) * 0.2
        ).round(2)

        # Emergency vulnerability index
        df["emergency_vulnerability_score"] = (
            (df["pop_density_per_sq_km"] / 1000.0) / (df["hospitals_count"] + 1)
        ).round(2)

        # Extract spatial bounds
        min_lat = float(df["latitude"].min())
        max_lat = float(df["latitude"].max())
        min_lon = float(df["longitude"].min())
        max_lon = float(df["longitude"].max())
        center_lat = round(float(df["latitude"].mean()), 4)
        center_lon = round(float(df["longitude"].mean()), 4)

        spatial_bounds = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
            "center_lat": center_lat,
            "center_lon": center_lon,
        }
        context.spatial_bounds = spatial_bounds
        context.normalized_df = df

        # Healthcare deserts (wards with zero hospital infrastructure)
        deserts = df[df["hospitals_count"] == 0].copy()
        context.healthcare_deserts = deserts

        total_pop = int(df["est_population_2026"].sum())
        median_density = float(df["pop_density_per_sq_km"].median())

        action_name = "Data Sanitization & Spatial Feature Indexing"
        observation_text = (
            f"Normalized {len(df)} nodes. Extracted spatial bounds "
            f"[({min_lat:.4f}, {min_lon:.4f}) to ({max_lat:.4f}, {max_lon:.4f})], "
            f"projected total 2026 population to {total_pop:,} across {len(df)} wards, "
            f"and isolated {len(deserts)} healthcare deserts (zero hospital facilities, "
            f"median density {median_density:,.0f}/km²)."
        )

        trace_entry = context.add_trace(
            agent=self.name,
            action=action_name,
            observation=observation_text,
            status="completed",
        )

        return {
            "node_count": len(df),
            "deserts_count": len(deserts),
            "spatial_bounds": spatial_bounds,
            "total_population_2026": total_pop,
            "trace": trace_entry,
        }
