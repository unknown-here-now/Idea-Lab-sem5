"""Input validation engine for spatial dataset ingestion and API parameters."""

import io
from typing import Any, List, Optional, Union
import numpy as np
import pandas as pd


class ValidationError(ValueError):
    """Raised when dataset schema, coordinate bounds, or optimization parameters are invalid."""
    pass


LAT_ALIASES: List[str] = ["latitude", "lat", "y", "wgs84_dd_n"]
LON_ALIASES: List[str] = ["longitude", "lon", "lng", "x", "wgs84_dd_e"]
AREA_ALIASES: List[str] = ["area", "area_sq_km", "area_km2", "sq_km", "shape_area"]
HH_ALIASES: List[str] = ["households", "hh", "total_households", "no_of_households"]
HOSP_ALIASES: List[str] = ["hospitals_count", "hospitals", "clinics", "health_centers", "medical", "hospital"]
POP_ALIASES: List[str] = ["population", "pop", "total_pop", "tot_pop", "total_population"]
WORK_ALIASES: List[str] = ["working_pop", "working_population", "workers", "employed"]


def validate_num_dark_stores(num_dark_stores: Any) -> int:
    """Validates that num_dark_stores is an integer and >= 1.
    
    Raises:
        ValidationError: If num_dark_stores is non-integer or < 1.
    """
    if num_dark_stores is None or (isinstance(num_dark_stores, str) and not num_dark_stores.strip()):
        return 3

    try:
        val = int(num_dark_stores)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid num_dark_stores '{num_dark_stores}': parameter must be an integer."
        )

    if val < 1:
        raise ValidationError(
            f"num_dark_stores must be greater than or equal to 1, received {val}."
        )

    return val


def validate_and_load_csv(content: Union[bytes, str]) -> pd.DataFrame:
    """Loads and validates a CSV payload from raw bytes or string.
    
    Raises:
        ValidationError: If content is empty, malformed, or missing required geospatial data.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    if not content or len(content.strip()) == 0:
        raise ValidationError("Uploaded CSV file is empty.")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except pd.errors.EmptyDataError:
        raise ValidationError("Uploaded CSV file is empty or contains no valid headers/data.")
    except Exception as e:
        raise ValidationError(f"Malformed CSV file format: {str(e)}")

    if df.empty or len(df) == 0:
        raise ValidationError("Dataset contains zero data rows.")

    return validate_dataframe(df)


def validate_and_load_file(content: Union[bytes, str], filename: str) -> pd.DataFrame:
    """Loads and validates a payload from raw bytes based on file extension.
    
    Supports: .csv, .xlsx, .xls, .geojson, .json
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
        
    if not content or len(content.strip()) == 0:
        raise ValidationError("Uploaded file is empty.")

    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(content))
        elif ext in ['geojson', 'json']:
            import json
            data = json.loads(content.decode("utf-8"))
            if "features" not in data:
                raise ValidationError("Invalid GeoJSON: missing 'features' array.")
            
            records = []
            for idx, feature in enumerate(data["features"]):
                geom = feature.get("geometry", {})
                props = feature.get("properties", {})
                
                if not geom or geom.get("type") != "Point":
                    continue # Skip non-point geometries for now
                
                coords = geom.get("coordinates", [None, None])
                if len(coords) >= 2:
                    props["longitude"] = coords[0]
                    props["latitude"] = coords[1]
                
                if "ward_id" not in props and "id" in feature:
                    props["ward_id"] = feature["id"]
                elif "ward_id" not in props:
                    props["ward_id"] = f"Custom_Ward_{idx+1}"
                    
                records.append(props)
                
            if not records:
                raise ValidationError("GeoJSON contains no valid Point features.")
                
            df = pd.DataFrame(records)
        else:
            # Fallback to CSV
            return validate_and_load_csv(content)
            
    except pd.errors.EmptyDataError:
        raise ValidationError("Uploaded file is empty or contains no valid headers/data.")
    except Exception as e:
        raise ValidationError(f"Malformed file format or parsing error: {str(e)}")

    if df.empty or len(df) == 0:
        raise ValidationError("Dataset contains zero data rows.")

    return validate_dataframe(df)


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validates dataframe schema, coordinate columns, and spatial bounds.
    
    Enforces:
        - Presence of latitude and longitude (via aliases)
        - Numeric coordinate values (no NaNs or non-numeric tokens)
        - WGS84 coordinate bounds: -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    
    Raises:
        ValidationError: If schema or coordinate bounds are violated.
    """
    if df.empty or len(df) == 0:
        raise ValidationError("Dataset contains zero data rows.")

    cols = {str(c).lower().strip(): c for c in df.columns}
    lat_col = next((cols[k] for k in LAT_ALIASES if k in cols), None)
    lon_col = next((cols[k] for k in LON_ALIASES if k in cols), None)

    if not lat_col or not lon_col:
        raise ValidationError(
            "Dataset missing geospatial reference: Latitude & Longitude required."
        )

    # Parse coordinates to numeric
    lat_series = pd.to_numeric(df[lat_col], errors="coerce")
    lon_series = pd.to_numeric(df[lon_col], errors="coerce")

    # Check for completely invalid coordinates
    if lat_series.isna().all() or lon_series.isna().all():
        raise ValidationError("All coordinate values in dataset are invalid or NaN.")

    # Check for partially invalid / non-numeric coordinates
    if lat_series.isna().any() or lon_series.isna().any():
        nan_count = int(lat_series.isna().sum() + lon_series.isna().sum())
        raise ValidationError(
            f"Coordinate columns contain {nan_count} non-numeric or missing (NaN) values."
        )

    # Check WGS84 geographic coordinate bounds
    if (lat_series < -90.0).any() or (lat_series > 90.0).any():
        out_of_bounds = df.loc[(lat_series < -90.0) | (lat_series > 90.0), lat_col].tolist()
        raise ValidationError(
            f"Coordinates out of valid bounds: Latitude must be between -90.0 and 90.0. "
            f"Found invalid values: {out_of_bounds[:5]}"
        )

    if (lon_series < -180.0).any() or (lon_series > 180.0).any():
        out_of_bounds = df.loc[(lon_series < -180.0) | (lon_series > 180.0), lon_col].tolist()
        raise ValidationError(
            f"Coordinates out of valid bounds: Longitude must be between -180.0 and 180.0. "
            f"Found invalid values: {out_of_bounds[:5]}"
        )

    validated_df = df.copy()
    validated_df["latitude"] = lat_series
    validated_df["longitude"] = lon_series

    return validated_df
