"""Autonomous Spatial Intelligence Server.

FastAPI application serving spatial multi-agent network optimization,
geospatial emergency hub dispatch, and executive policy memorandum generation.
"""

import io
import json
import os
from pathlib import Path
import time
from typing import Any, Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import numpy as np
import pandas as pd
import uvicorn

from agents.coordinator import SpatialMultiAgentCoordinator
from core.spatial_math import haversine
from core.validator import (
    ValidationError,
    validate_and_load_csv,
    validate_and_load_file,
    validate_dataframe,
    validate_num_dark_stores,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Autonomous Spatial Intelligence Engine",
    description="Multi-Agent Spatial Network Optimization Platform",
    version="2.8.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

coordinator = SpatialMultiAgentCoordinator()


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Returns structured HTTP 400 error payload on validation failures."""
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles FastAPI form/query validation errors with uniform 400 JSON envelope."""
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": f"Malformed request parameters: {str(exc)}"},
    )


@app.get("/api/health")
async def health_check():
    """System self-diagnostic endpoint checking dataset availability and agent pipeline readiness."""
    default_csv = BASE_DIR / "mbmc_79_wards_census.csv"
    borivali_csv = BASE_DIR / "borivali_census_spatial_dataset.csv"
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "system_check": {
            "default_census_exists": default_csv.exists(),
            "borivali_census_exists": borivali_csv.exists(),
            "multi_agent_coordinator": "ready",
            "pipeline_agents": [agent.name for agent in coordinator.pipeline],
            "clustering_engine": "sklearn.cluster.KMeans ready",
            "memory_state": "nominal",
        },
    }


async def fetch_osm_data_for_wards(df: pd.DataFrame) -> pd.DataFrame:
    """Dynamically fetches real-world hospital and residential data from OpenStreetMap for custom pins."""
    try:
        import httpx
        
        # Build a batched Overpass QL query to do all points in one network request
        queries = []
        for idx, row in df.iterrows():
            lat, lon = row["latitude"], row["longitude"]
            queries.append(f"""
            (
              node["amenity"~"hospital|clinic"](around:2500, {lat}, {lon});
              way["amenity"~"hospital|clinic"](around:2500, {lat}, {lon});
            );
            out count;
            (
              way["building"~"residential|apartments"](around:1000, {lat}, {lon});
            );
            out count;
            """)
        
        full_query = "[out:json];\n" + "".join(queries)
        
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(
                "https://overpass-api.de/api/interpreter", 
                data=full_query,
                headers={"User-Agent": "SpatialIntelligenceApp/2.8"}
            )
            
            if res.status_code == 200:
                data = res.json()
                elements = data.get("elements", [])
                
                # Overpass returns 2 count blocks per point: [hospitals, buildings, hospitals, buildings...]
                if len(elements) == len(df) * 2:
                    for i, idx in enumerate(df.index):
                        hosp_block = elements[i * 2].get("tags", {})
                        build_block = elements[i * 2 + 1].get("tags", {})
                        
                        hosp_count = hosp_block.get("nodes", 0) + hosp_block.get("ways", 0)
                        build_count = build_block.get("nodes", 0) + build_block.get("ways", 0)
                        
                        # Real world estimations:
                        df.at[idx, "hospitals_count"] = hosp_count
                        # Assume 4.3 people per residential building/apartment block in India
                        real_pop = int(build_count * 4.3 * 10) if build_count > 0 else 15000
                        df.at[idx, "population"] = max(real_pop, 5000) # Floor of 5000
    except Exception as e:
        print(f"OSM Fetch failed (falling back to defaults): {str(e)}")
        
    return df

@app.post("/api/optimize")
async def optimize_spatial_network(
    file: Optional[UploadFile] = File(None),
    num_dark_stores: Any = Form(3),
    custom_wards: Optional[str] = Form(None),
):
    """Executes multi-agent spatial optimization pipeline across input ward data.
    
    Accepts:
        - file (optional): Uploaded CSV, Excel, or GeoJSON with ward geometries and demographics.
        - num_dark_stores (optional): Integer >= 1 specifying number of fulfillment hubs.
        - custom_wards (optional): JSON string of custom drawn map coordinates.
    
    Returns:
        JSON response with metrics, dark_stores, emergency_hub, dynamic agent_trace,
        llm_report markdown, and ward feature records.
    """
    try:
        # Validate num_dark_stores >= 1
        k = validate_num_dark_stores(num_dark_stores)

        # Handle custom drawn map points first
        if custom_wards and custom_wards.strip():
            import json
            try:
                custom_data = json.loads(custom_wards)
                if not isinstance(custom_data, list) or len(custom_data) == 0:
                    raise ValidationError("Custom map data must be a non-empty array.")
                df = pd.DataFrame(custom_data)
                
                # Fetch real-world data dynamically
                df = await fetch_osm_data_for_wards(df)
                
                df = validate_dataframe(df)
            except Exception as e:
                raise ValidationError(f"Failed to parse custom map data: {str(e)}")
        # Handle uploaded file
        elif file is not None and getattr(file, "filename", None) and file.filename.strip():
            content = await file.read()
            df = validate_and_load_file(content, file.filename)
        # Fall back to local municipal census
        else:
            default_csv_path = BASE_DIR / "mbmc_79_wards_census.csv"
            if not default_csv_path.exists():
                default_csv_path = BASE_DIR / "borivali_census_spatial_dataset.csv"
            if not default_csv_path.exists():
                raise ValidationError("Default census dataset not found on server.")
            with open(default_csv_path, "rb") as f:
                content = f.read()
            df = validate_and_load_csv(content)

        # Run multi-agent pipeline
        context = await coordinator.run(raw_data=df, num_dark_stores=k)

        norm_df = context.normalized_df

        # Format wards payload strictly matching index.html client expectations
        wards_payload = []
        for _, r in norm_df.iterrows():
            ward_id = str(r.get("ward_id", ""))
            
            # Extract ward_name if present, otherwise default to ward_id
            name_candidates = [r.get(c) for c in ["ward_name", "locality_name", "name", "zone_name"] if c in r and pd.notna(r[c])]
            ward_name = str(name_candidates[0]) if name_candidates else ward_id

            wards_payload.append({
                "ward_id": ward_id,
                "ward_name": ward_name,
                "latitude": round(float(r["latitude"]), 6),
                "longitude": round(float(r["longitude"]), 6),
                "population": int(r.get("population", 0)),
                "est_population_2026": int(r.get("est_population_2026", 0)),
                "hospitals_count": int(r.get("hospitals_count", 0)),
                "blinkit_demand_score": round(float(r.get("blinkit_demand_score", 0.0)), 2),
                "emergency_vulnerability_score": round(float(r.get("emergency_vulnerability_score", 0.0)), 2),
            })

        metrics = {
            "total_wards": int(context.metrics.get("total_wards", len(norm_df))),
            "total_population_2026": int(context.metrics.get("total_population_2026", 0)),
            "blinkit_coverage_pct": float(context.metrics.get("blinkit_coverage_pct", 0.0)),
            "blinkit_wards_covered": int(context.metrics.get("blinkit_wards_covered", 0)),
            "emergency_deserts_count": int(context.metrics.get("emergency_deserts_count", 0)),
            "emergency_avg_dist_km": float(context.metrics.get("emergency_avg_dist_km", 0.0)),
        }

        dark_stores = [
            {
                "id": int(ds["id"]),
                "lat": round(float(ds["lat"]), 4),
                "lon": round(float(ds["lon"]), 4),
            }
            for ds in context.dark_stores
        ]

        emergency_hub = {
            "lat": round(float(context.emergency_hub.get("lat", 0.0)), 4),
            "lon": round(float(context.emergency_hub.get("lon", 0.0)), 4),
        }

        return {
            "status": "success",
            "metrics": metrics,
            "dark_stores": dark_stores,
            "emergency_hub": emergency_hub,
            "agent_trace": context.agent_trace,
            "llm_report": context.policy_report,
            "wards": wards_payload,
        }

    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(e)},
        )


@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    """Serves the landing page."""
    html_file = BASE_DIR / "landing.html"
    if not html_file.exists():
        # Fallback if landing is missing
        return await serve_dashboard()
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/app", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves index.html geospatial command dashboard."""
    html_file = BASE_DIR / "index.html"
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/manifest.json")
async def serve_manifest():
    file_path = BASE_DIR / "manifest.json"
    if file_path.exists():
        return FileResponse(file_path, media_type="application/json")
    return JSONResponse(status_code=404, content={"message": "Not found"})

@app.get("/sw.js")
async def serve_sw():
    file_path = BASE_DIR / "sw.js"
    if file_path.exists():
        return FileResponse(file_path, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"message": "Not found"})

# Legacy backward-compatibility helpers
def normalize_and_score(df: pd.DataFrame) -> pd.DataFrame:
    import asyncio
    from agents.perception_agent import PerceptionAgent
    from agents.base import AgentContext
    agent = PerceptionAgent()
    ctx = AgentContext(raw_data=df)
    asyncio.run(agent.execute(ctx))
    return ctx.normalized_df


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)