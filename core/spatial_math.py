"""Geospatial mathematical primitives and distance calculations."""

from math import asin, cos, radians, sin, sqrt


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points on the Earth surface (WGS84) in kilometers.
    
    Guarantees numerical stability against domain errors in asin().
    """
    r = 6371.0  # Earth's radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2.0) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2.0) ** 2
    )
    # Clamp to [0.0, 1.0] to prevent floating point imprecision causing math domain errors in sqrt/asin
    a = min(1.0, max(0.0, a))
    return 2.0 * r * asin(sqrt(a))
