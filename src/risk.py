"""Aeronautical risk calculation along flight routes."""

import numpy as np

from src.config import (
    CONVECTION_PRECIP_THRESHOLD,
    ICING_HYDROMETEOR_THRESHOLD,
    WIND_SHEAR_HORIZONTAL_THRESHOLD,
    WIND_SHEAR_VERTICAL_THRESHOLD,
)
from src import wrf_processing

# Additional threshold for vertical velocity convection indicator
CONVECTION_W_THRESHOLD = 1.5  # m/s


def _enrich_profile_with_grid_indices(profile: list[dict]) -> list[dict]:
    """Pre-calculate and cache nearest grid point index for each profile point."""
    for point in profile:
        if "grid_idx" not in point:
            point["grid_idx"] = wrf_processing.find_nearest_grid_point(point["lat"], point["lon"])
    return profile


def _collect_distinct_times(profile: list[dict]) -> set[int]:
    """Collect all distinct time indices referenced by profile points."""
    times = set()
    for point in profile:
        times.add(point.get("time_idx_left", 0))
        times.add(point.get("time_idx_right", 0))
    return times


def _interpolate_temporal(val0: float, val1: float, frac: float) -> float:
    """Linearly interpolate between two time-indexed values."""
    return (1.0 - frac) * val0 + frac * val1


def compute_icing_risk(profile: list[dict]) -> list[bool]:
    """Compute icing risk along route with temporal interpolation.

    Icing risk exists where T < 0 C and hydrometeors are present.
    Includes Cloud Water (QCLOUD), Rain Water (QRAIN), Ice (QICE), Snow (QSNOW), and Graupel (QGRAUP).
    """
    _enrich_profile_with_grid_indices(profile)
    risks = []
    distinct_times = _collect_distinct_times(profile)

    temp_cache = {}
    for t in distinct_times:
        temp_cache[t] = wrf_processing.compute_temperature_celsius(t).values

    hydro_cache = {}
    for t in distinct_times:
        hydro_cache[t] = wrf_processing.get_hydrometeors(t)

    n_levels = next(iter(temp_cache.values())).shape[0] if temp_cache else 47

    for point in profile:
        lat_idx, lon_idx = point["grid_idx"]
        flight_level_left = min(point.get("level_idx_left", 0), n_levels - 1)
        flight_level_right = min(point.get("level_idx_right", 0), n_levels - 1)

        t_left = point.get("time_idx_left", 0)
        t_right = point.get("time_idx_right", 0)
        t_frac = point.get("time_frac", 0.0)

        temp0 = temp_cache[t_left][flight_level_left, lat_idx, lon_idx]
        if t_left != t_right and t_frac > 0:
            temp1 = temp_cache[t_right][flight_level_right, lat_idx, lon_idx]
            temp_at_point = _interpolate_temporal(float(temp0), float(temp1), t_frac)
        else:
            temp_at_point = float(temp0)

        hl = hydro_cache[t_left]
        qcloud0 = float(hl["qcloud"][flight_level_left, lat_idx, lon_idx])
        qrain0 = float(hl["qrain"][flight_level_left, lat_idx, lon_idx])
        qice0 = float(hl["qice"][flight_level_left, lat_idx, lon_idx])
        qsnow0 = float(hl["qsnow"][flight_level_left, lat_idx, lon_idx])
        qgraupel0 = float(hl["qgraupel"][flight_level_left, lat_idx, lon_idx])

        if t_left != t_right and t_frac > 0:
            hr = hydro_cache[t_right]
            qcloud1 = float(hr["qcloud"][flight_level_right, lat_idx, lon_idx])
            qrain1 = float(hr["qrain"][flight_level_right, lat_idx, lon_idx])
            qice1 = float(hr["qice"][flight_level_right, lat_idx, lon_idx])
            qsnow1 = float(hr["qsnow"][flight_level_right, lat_idx, lon_idx])
            qgraupel1 = float(hr["qgraupel"][flight_level_right, lat_idx, lon_idx])

            qcloud_val = _interpolate_temporal(qcloud0, qcloud1, t_frac)
            qrain_val = _interpolate_temporal(qrain0, qrain1, t_frac)
            qice_val = _interpolate_temporal(qice0, qice1, t_frac)
            qsnow_val = _interpolate_temporal(qsnow0, qsnow1, t_frac)
            qgraupel_val = _interpolate_temporal(qgraupel0, qgraupel1, t_frac)
        else:
            qcloud_val = qcloud0
            qrain_val = qrain0
            qice_val = qice0
            qsnow_val = qsnow0
            qgraupel_val = qgraupel0

        has_hydrometeors = (
            qcloud_val > ICING_HYDROMETEOR_THRESHOLD
            or qrain_val > ICING_HYDROMETEOR_THRESHOLD
            or qice_val > ICING_HYDROMETEOR_THRESHOLD
            or qsnow_val > ICING_HYDROMETEOR_THRESHOLD
            or qgraupel_val > ICING_HYDROMETEOR_THRESHOLD
        )
        risks.append(temp_at_point < 0.0 and has_hydrometeors)

    return risks


def compute_wind_shear_risk(profile: list[dict]) -> list[bool]:
    """Compute wind shear risk along route with temporal interpolation.

    Checks both vertical and horizontal wind gradients.
    """
    _enrich_profile_with_grid_indices(profile)
    risks = []
    distinct_times = _collect_distinct_times(profile)

    u_cache = {}
    v_cache = {}
    z_cache = {}
    for t in distinct_times:
        ds = wrf_processing.get_dataset(t)
        u_cache[t] = wrf_processing.destagger_u(ds["U"]).isel(Time=0).values
        v_cache[t] = wrf_processing.destagger_v(ds["V"]).isel(Time=0).values
        z_cache[t] = wrf_processing.compute_geopotential_height(t).values

    n_levels = next(iter(u_cache.values())).shape[0] if u_cache else 47

    prev_u = None
    prev_v = None

    for i, point in enumerate(profile):
        lat_idx, lon_idx = point["grid_idx"]
        flight_level_left = min(point.get("level_idx_left", 0), n_levels - 1)
        flight_level_right = min(point.get("level_idx_right", 0), n_levels - 1)

        t_left = point.get("time_idx_left", 0)
        t_right = point.get("time_idx_right", 0)
        t_frac = point.get("time_frac", 0.0)

        u0 = float(u_cache[t_left][flight_level_left, lat_idx, lon_idx])
        v0 = float(v_cache[t_left][flight_level_left, lat_idx, lon_idx])
        if t_left != t_right and t_frac > 0:
            u1 = float(u_cache[t_right][flight_level_right, lat_idx, lon_idx])
            v1 = float(v_cache[t_right][flight_level_right, lat_idx, lon_idx])
            u_at_point = _interpolate_temporal(u0, u1, t_frac)
            v_at_point = _interpolate_temporal(v0, v1, t_frac)
        else:
            u_at_point = u0
            v_at_point = v0

        shear_detected = False

        if prev_u is not None and i > 0:
            du = abs(u_at_point - prev_u)
            dv = abs(v_at_point - prev_v)
            dx_km = profile[i]["distance_km"] - profile[i - 1]["distance_km"]
            if dx_km > 0.01:
                dx_m = dx_km * 1000.0
                if np.sqrt(du**2 + dv**2) / dx_m > WIND_SHEAR_HORIZONTAL_THRESHOLD:
                    shear_detected = True

        if n_levels > 1:
            level_below_left = max(0, flight_level_left - 1)
            level_above_left = min(flight_level_left + 1, n_levels - 1)
            level_below_right = max(0, flight_level_right - 1)
            level_above_right = min(flight_level_right + 1, n_levels - 1)

            zu0 = float(z_cache[t_left][level_below_left, lat_idx, lon_idx])
            za0 = float(z_cache[t_left][level_above_left, lat_idx, lon_idx])
            ub0 = float(u_cache[t_left][level_below_left, lat_idx, lon_idx])
            ua0 = float(u_cache[t_left][level_above_left, lat_idx, lon_idx])
            vb0 = float(v_cache[t_left][level_below_left, lat_idx, lon_idx])
            va0 = float(v_cache[t_left][level_above_left, lat_idx, lon_idx])

            if t_left != t_right and t_frac > 0:
                zu1 = float(z_cache[t_right][level_below_right, lat_idx, lon_idx])
                za1 = float(z_cache[t_right][level_above_right, lat_idx, lon_idx])
                ub1 = float(u_cache[t_right][level_below_right, lat_idx, lon_idx])
                ua1 = float(u_cache[t_right][level_above_right, lat_idx, lon_idx])
                vb1 = float(v_cache[t_right][level_below_right, lat_idx, lon_idx])
                va1 = float(v_cache[t_right][level_above_right, lat_idx, lon_idx])

                z_below = _interpolate_temporal(zu0, zu1, t_frac)
                z_above = _interpolate_temporal(za0, za1, t_frac)
                u_below = _interpolate_temporal(ub0, ub1, t_frac)
                u_above = _interpolate_temporal(ua0, ua1, t_frac)
                v_below = _interpolate_temporal(vb0, vb1, t_frac)
                v_above = _interpolate_temporal(va0, va1, t_frac)
            else:
                z_below = zu0
                z_above = za0
                u_below = ub0
                u_above = ua0
                v_below = vb0
                v_above = va0

            dz = abs(z_above - z_below)
            if dz > 1.0:
                du_v = abs(u_above - u_below)
                dv_v = abs(v_above - v_below)
                if np.sqrt(du_v**2 + dv_v**2) / dz > WIND_SHEAR_VERTICAL_THRESHOLD:
                    shear_detected = True

        risks.append(shear_detected)
        prev_u = u_at_point
        prev_v = v_at_point

    return risks


def compute_convection_visibility_risk(profile: list[dict]) -> list[bool]:
    """Compute approximate convection/visibility risk at airports only.

    Visibility matters at departure and arrival airports, not en route.
    Uses precipitation rate and total hydrometeors, along with vertical velocity (W),
    to identify strong convective hazards.
    """
    _enrich_profile_with_grid_indices(profile)
    risks = [False] * len(profile)
    distinct_times = _collect_distinct_times(profile)

    precip_cache = {}
    hydro_cache = {}
    w_cache = {}
    for t in distinct_times:
        precip_cache[t] = wrf_processing.compute_precipitation(t)
        hydro_cache[t] = wrf_processing.get_hydrometeors(t)
        w_cache[t] = wrf_processing.get_w_field(t)

    times_min = wrf_processing.get_times_minutes()
    n_levels = next(iter(hydro_cache.values()))["qcloud"].shape[0] if hydro_cache else 47

    airport_indices = [0, len(profile) - 1]

    for idx in airport_indices:
        point = profile[idx]
        lat_idx, lon_idx = point["grid_idx"]
        flight_level_left = min(point.get("level_idx_left", 0), n_levels - 1)
        flight_level_right = min(point.get("level_idx_right", 0), n_levels - 1)

        t_left = point.get("time_idx_left", 0)
        t_right = point.get("time_idx_right", 0)

        if t_left != t_right:
            p_left = float(precip_cache[t_left][lat_idx, lon_idx])
            p_right = float(precip_cache[t_right][lat_idx, lon_idx])
            dt_seconds = (times_min[t_right] - times_min[t_left]) * 60.0
            precip_rate = (p_right - p_left) / dt_seconds if dt_seconds > 0 else 0.0
        else:
            precip_rate = 0.0

        hl = hydro_cache[t_left]
        qc0 = float(hl["qcloud"][flight_level_left, lat_idx, lon_idx])
        qr0 = float(hl["qrain"][flight_level_left, lat_idx, lon_idx])
        qg0 = float(hl["qgraupel"][flight_level_left, lat_idx, lon_idx])
        w0 = float(w_cache[t_left][flight_level_left, lat_idx, lon_idx])

        t_frac = point.get("time_frac", 0.0)
        if t_left != t_right and t_frac > 0:
            hr = hydro_cache[t_right]
            qc1 = float(hr["qcloud"][flight_level_right, lat_idx, lon_idx])
            qr1 = float(hr["qrain"][flight_level_right, lat_idx, lon_idx])
            qg1 = float(hr["qgraupel"][flight_level_right, lat_idx, lon_idx])
            w1 = float(w_cache[t_right][flight_level_right, lat_idx, lon_idx])

            qc_val = _interpolate_temporal(qc0, qc1, t_frac)
            qr_val = _interpolate_temporal(qr0, qr1, t_frac)
            qg_val = _interpolate_temporal(qg0, qg1, t_frac)
            w_val = _interpolate_temporal(w0, w1, t_frac)
        else:
            qc_val = qc0
            qr_val = qr0
            qg_val = qg0
            w_val = w0

        total_hydro = qc_val + qr_val + qg_val

        risk = (
            precip_rate > CONVECTION_PRECIP_THRESHOLD
            or total_hydro > ICING_HYDROMETEOR_THRESHOLD * 10
            or abs(w_val) > CONVECTION_W_THRESHOLD
        )
        risks[idx] = risk

    return risks


def compute_all_risks(profile: list[dict]) -> dict[str, list[bool]]:
    """Compute all risk types along the route with temporal interpolation."""
    _enrich_profile_with_grid_indices(profile)
    return {
        "icing": compute_icing_risk(profile),
        "wind_shear": compute_wind_shear_risk(profile),
        "convection_visibility": compute_convection_visibility_risk(profile),
    }
