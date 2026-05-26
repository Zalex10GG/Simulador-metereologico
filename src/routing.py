"""Route calculation: great-circle paths and flight profiles."""

import math

import numpy as np

from src.config import CRUISE_SPEED_KMH, ROUTE_NUM_POINTS


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def great_circle_points(
    lat1: float, lon1: float, lat2: float, lon2: float, num_points: int = ROUTE_NUM_POINTS
) -> list[dict]:
    """Generate great-circle route points between origin and destination.

    Returns list of dicts with lat, lon, distance_km from origin.
    """
    points = []
    total_dist = haversine_km(lat1, lon1, lat2, lon2)
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)
    angular_dist = total_dist / 6371.0

    for i in range(num_points):
        f = i / (num_points - 1) if num_points > 1 else 0.0

        if angular_dist > 1e-10:
            A = math.sin((1 - f) * angular_dist) / math.sin(angular_dist)
            B = math.sin(f * angular_dist) / math.sin(angular_dist)
        else:
            A = 1.0 - f
            B = f

        x = A * math.cos(lat1_r) * math.cos(lon1_r) + B * math.cos(lat2_r) * math.cos(lon2_r)
        y = A * math.cos(lat1_r) * math.sin(lon1_r) + B * math.cos(lat2_r) * math.sin(lon2_r)
        z = A * math.sin(lat1_r) + B * math.sin(lat2_r)

        lat_gc = math.degrees(math.atan2(z, math.sqrt(x**2 + y**2)))
        lon_gc = math.degrees(math.atan2(y, x))

        dist_km = f * total_dist
        points.append({"lat": lat_gc, "lon": lon_gc, "distance_km": dist_km})

    return points


def compute_flight_profile(
    route_points: list[dict], total_distance_km: float, cruise_level_m: float = 10058.4
) -> list[dict]:
    """Compute vertical flight profile for route points.

    First 20%: linear ascent from surface to cruise level.
    Middle 60%: cruise at cruise level.
    Last 20%: linear descent from cruise level to surface.
    """
    profile = []
    for point in route_points:
        frac = point["distance_km"] / total_distance_km if total_distance_km > 0 else 0.0

        if frac <= 0.2:
            altitude = (frac / 0.2) * cruise_level_m
        elif frac <= 0.8:
            altitude = cruise_level_m
        else:
            altitude = ((1.0 - frac) / 0.2) * cruise_level_m

        profile.append({
            "lat": point["lat"],
            "lon": point["lon"],
            "distance_km": point["distance_km"],
            "altitude_m": altitude,
        })

    return profile


def compute_flight_time_minutes(distance_km: float) -> float:
    """Compute flight time in minutes at cruise speed."""
    hours = distance_km / CRUISE_SPEED_KMH
    return hours * 60.0


def validate_route_in_domain(
    route_points: list[dict],
    domain_bounds: dict,
) -> tuple[bool, str]:
    """Check if all route points are within WRF domain.

    Returns (is_valid, error_message).
    """
    for p in route_points:
        lat_ok = domain_bounds["lat_min"] <= p["lat"] <= domain_bounds["lat_max"]
        lon_ok = domain_bounds["lon_min"] <= p["lon"] <= domain_bounds["lon_max"]
        if not (lat_ok and lon_ok):
            return False, f"Route point ({p['lat']:.2f}, {p['lon']:.2f}) is outside WRF domain"
    return True, ""
