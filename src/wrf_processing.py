"""WRF NetCDF processing: opening, diagnostics, and interpolation."""

import glob
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import xarray as xr
import xwrf

from src.config import G, GAMMA, P0, R_CP, R_DRY, WRF_FILE_PATTERN, DATA_DIR

_datasets: list[xr.Dataset] = []
_times: list[datetime] = []


def _scan_and_load() -> None:
    """Scan the data directory and load WRF snapshot files sorted by timestamp."""
    global _datasets, _times
    if _datasets:
        return

    pattern = str(DATA_DIR / WRF_FILE_PATTERN)
    files = sorted(glob.glob(pattern))

    # Filter out old 2009 multi-timestep files
    files = [f for f in files if "d01_2009" not in f]

    if not files:
        raise RuntimeError(f"No WRF snapshot files matching '{WRF_FILE_PATTERN}' found in {DATA_DIR}")

    for filepath in files:
        ds = xr.open_dataset(filepath, engine="netcdf4")
        if hasattr(ds, "xwrf"):
            _ = ds.xwrf
        _datasets.append(ds)

        # Parse timestamp from filename, format: wrfout_YYYY-MM-DD_HH_MM_SS.nc
        basename = Path(filepath).stem
        match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2})', basename)
        if match:
            dt = datetime.strptime(match.group(1), "%Y-%m-%d_%H_%M_%S")
        else:
            # Fallback to Times variable
            t_bytes = ds["Times"].values[0]
            t_str = t_bytes.decode("utf-8").strip()
            dt = datetime.strptime(t_str.replace("_", " "), "%Y-%m-%d %H:%M:%S")

        _times.append(dt)


def get_dataset(time_index: int = 0) -> xr.Dataset:
    """Return the cached WRF dataset for a specific time index."""
    _scan_and_load()
    if time_index < 0 or time_index >= len(_datasets):
        raise IndexError(f"Time index {time_index} out of range [0, {len(_datasets)-1}]")
    return _datasets[time_index]


def get_dimensions() -> dict:
    """Return dataset dimensions of the first dataset."""
    ds = get_dataset(0)
    return dict(ds.sizes)


def get_times() -> list[str]:
    """Return list of time strings from the datasets."""
    _scan_and_load()
    return [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in _times]


def get_coordinates() -> tuple[np.ndarray, np.ndarray]:
    """Return XLAT and XLONG 2D arrays from the first dataset."""
    ds = get_dataset(0)
    lat = ds["XLAT"].values[0]
    lon = ds["XLONG"].values[0]
    return lat, lon


def get_domain_bounds() -> dict:
    """Return WRF domain bounding box."""
    lat, lon = get_coordinates()
    return {
        "lat_min": float(lat.min()),
        "lat_max": float(lat.max()),
        "lon_min": float(lon.min()),
        "lon_max": float(lon.max()),
    }


def compute_pressure(time_index: int = 0) -> xr.DataArray:
    """Compute total pressure P + PB at a time index."""
    ds = get_dataset(time_index)
    return ds["P"].isel(Time=0) + ds["PB"].isel(Time=0)


def compute_geopotential_height(time_index: int = 0) -> xr.DataArray:
    """Compute geopotential height (PH + PHB) / g, averaged to mass levels."""
    ds = get_dataset(time_index)
    ph_full = ds["PH"].isel(Time=0) + ds["PHB"].isel(Time=0)
    ph_mass = 0.5 * (ph_full.isel(bottom_top_stag=slice(None, -1)) + ph_full.isel(bottom_top_stag=slice(1, None)))
    return ph_mass / G


def compute_potential_temperature(time_index: int = 0) -> xr.DataArray:
    """Compute potential temperature from WRF perturbation T + 300."""
    ds = get_dataset(time_index)
    return ds["T"].isel(Time=0) + 300.0


def compute_temperature(time_index: int = 0) -> xr.DataArray:
    """Compute absolute temperature from potential temperature using Poisson equation."""
    theta = compute_potential_temperature(time_index)
    p = compute_pressure(time_index)
    return theta * (p / P0) ** R_CP


def compute_temperature_celsius(time_index: int = 0) -> xr.DataArray:
    """Compute temperature in Celsius."""
    return compute_temperature(time_index) - 273.15


def destagger_u(u: xr.DataArray) -> xr.DataArray:
    """Destagger U variable to mass points."""
    return 0.5 * (u.isel(west_east_stag=slice(None, -1)) + u.isel(west_east_stag=slice(1, None)))


def destagger_v(v: xr.DataArray) -> xr.DataArray:
    """Destagger V variable to mass points."""
    return 0.5 * (v.isel(south_north_stag=slice(None, -1)) + v.isel(south_north_stag=slice(1, None)))


def compute_wind_speed_10m(time_index: int = 0) -> np.ndarray:
    """Compute 10m wind speed magnitude."""
    ds = get_dataset(time_index)
    u10 = ds["U10"].isel(Time=0).values
    v10 = ds["V10"].isel(Time=0).values
    return np.sqrt(u10**2 + v10**2)


def compute_surface_pressure(time_index: int = 0) -> np.ndarray:
    """Return surface pressure PSFC."""
    ds = get_dataset(time_index)
    return ds["PSFC"].isel(Time=0).values


def compute_temperature_2m(time_index: int = 0) -> np.ndarray:
    """Return 2m temperature in Celsius."""
    ds = get_dataset(time_index)
    return ds["T2"].isel(Time=0).values - 273.15


def compute_precipitation(time_index: int = 0) -> np.ndarray:
    """Compute accumulated precipitation RAINC + RAINNC."""
    ds = get_dataset(time_index)
    return ds["RAINC"].isel(Time=0).values + ds["RAINNC"].isel(Time=0).values


def compute_mslp(time_index: int = 0) -> np.ndarray:
    """Reduce surface pressure to mean sea level using the barometric formula.

    Uses PSFC, terrain height HGT, and 2m temperature T2 with a standard
    lapse rate (gamma = 0.0065 K/m) for the reduction.
    MSLP = PSFC * exp( g * HGT / (R_d * T_virtual) )
    """
    ds = get_dataset(time_index)
    psfc = ds["PSFC"].isel(Time=0).values
    hgt = ds["HGT"].isel(Time=0).values
    t2 = ds["T2"].isel(Time=0).values

    t_virtual = t2 + 0.5 * GAMMA * hgt
    t_virtual = np.maximum(t_virtual, 250.0)
    exponent = (G * hgt) / (R_DRY * t_virtual)
    exponent = np.minimum(exponent, 5.0)
    mslp = psfc * np.exp(exponent)
    return mslp


def _interpolate_vertical(p_full: np.ndarray, var_full: np.ndarray, p_target: float) -> np.ndarray:
    """Vectorized linear interpolation of var_full along axis 0 based on pressure p_full matching p_target."""
    n_levels, n_lat, n_lon = p_full.shape
    idx = np.sum(p_full >= p_target, axis=0)

    result = np.full((n_lat, n_lon), np.nan)

    valid = (idx > 0) & (idx < n_levels)
    if np.any(valid):
        k1 = idx - 1
        k2 = idx

        # Create coordinate grids for advanced indexing
        ii, jj = np.meshgrid(np.arange(n_lat), np.arange(n_lon), indexing='ij')

        valid_ii = ii[valid]
        valid_jj = jj[valid]
        valid_k1 = k1[valid]
        valid_k2 = k2[valid]

        p1 = p_full[valid_k1, valid_ii, valid_jj]
        p2 = p_full[valid_k2, valid_ii, valid_jj]

        v1 = var_full[valid_k1, valid_ii, valid_jj]
        v2 = var_full[valid_k2, valid_ii, valid_jj]

        dp = p2 - p1
        dp_nonzero = np.where(dp == 0, 1.0, dp)
        frac = (p_target - p1) / dp_nonzero
        v_interp_val = v1 + frac * (v2 - v1)

        v_interp_val = np.where(dp == 0, np.nan, v_interp_val)
        result[valid] = v_interp_val

    return result


def get_field_at_pressure_level(
    var_name: str,
    pressure_level_hpa: float,
    time_index: int = 0,
) -> np.ndarray:
    """Interpolate a 3D field to a constant pressure level.

    Uses linear interpolation in the vertical using full pressure levels.
    """
    ds = get_dataset(time_index)
    pressure = compute_pressure(time_index)

    if var_name == "PH":
        var_full = compute_geopotential_height(time_index).values
    elif var_name == "T":
        var_full = compute_temperature(time_index).values
    else:
        var_full = ds[var_name].isel(Time=0).values

    p_full = pressure.values
    p_target = pressure_level_hpa * 100.0

    return _interpolate_vertical(p_full, var_full, p_target)


def get_wind_at_pressure_level(
    pressure_level_hpa: float,
    time_index: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (u, v, wind_speed) at a pressure level."""
    ds = get_dataset(time_index)

    u_full = destagger_u(ds["U"]).isel(Time=0).values
    v_full = destagger_v(ds["V"]).isel(Time=0).values
    p_full = compute_pressure(time_index).values

    p_target = pressure_level_hpa * 100.0

    u_interp = _interpolate_vertical(p_full, u_full, p_target)
    v_interp = _interpolate_vertical(p_full, v_full, p_target)

    speed = np.sqrt(u_interp**2 + v_interp**2)
    return u_interp, v_interp, speed


def get_vertical_profile(lat_idx: int, lon_idx: int, time_index: int = 0) -> dict:
    """Return vertical profile of key variables at a grid point."""
    ds = get_dataset(time_index)
    pressure = compute_pressure(time_index).isel(south_north=lat_idx, west_east=lon_idx)
    temp = compute_temperature(time_index).isel(south_north=lat_idx, west_east=lon_idx)
    z = compute_geopotential_height(time_index).isel(south_north=lat_idx, west_east=lon_idx)

    u = destagger_u(ds["U"]).isel(Time=0, south_north=lat_idx, west_east=lon_idx)
    v = destagger_v(ds["V"]).isel(Time=0, south_north=lat_idx, west_east=lon_idx)
    qv = ds["QVAPOR"].isel(Time=0, south_north=lat_idx, west_east=lon_idx).values

    # Calcular dewpoint usando MetPy
    import metpy.calc as mpcalc
    from metpy.units import units
    p_val = pressure.values * units.Pa
    t_val = temp.values * units.kelvin
    qv_val = qv * units('kg/kg')
    q_val = qv_val / (1.0 + qv_val)
    try:
        td_val = mpcalc.dewpoint_from_specific_humidity(p_val, t_val, q_val)
        td = td_val.to(units.kelvin).magnitude
    except Exception:
        # Fallback simple si falla MetPy
        td = temp.values - 5.0

    return {
        "pressure": pressure.values,
        "temperature": temp.values,
        "dewpoint": td,
        "geopotential_height": z.values,
        "u_wind": u.values,
        "v_wind": v.values,
    }



def find_nearest_grid_point(lat: float, lon: float) -> tuple[int, int]:
    """Find nearest grid point indices for given lat/lon using squared Euclidean distance."""
    lat_grid, lon_grid = get_coordinates()
    lat_diff = lat_grid - lat
    lon_diff = lon_grid - lon
    combined = lat_diff**2 + lon_diff**2
    idx = np.unravel_index(np.argmin(combined), combined.shape)
    return int(idx[0]), int(idx[1])


def is_in_domain(lat: float, lon: float) -> bool:
    """Check if lat/lon is within the WRF domain."""
    bounds = get_domain_bounds()
    return (
        bounds["lat_min"] <= lat <= bounds["lat_max"]
        and bounds["lon_min"] <= lon <= bounds["lon_max"]
    )


def get_hydrometeors(time_index: int = 0) -> dict[str, np.ndarray]:
    """Return hydrometeor fields at a time index."""
    ds = get_dataset(time_index)
    return {
        "qvapor": ds["QVAPOR"].isel(Time=0).values,
        "qcloud": ds["QCLOUD"].isel(Time=0).values,
        "qrain": ds["QRAIN"].isel(Time=0).values,
        "qice": ds["QICE"].isel(Time=0).values,
        "qsnow": ds["QSNOW"].isel(Time=0).values,
        "qgraupel": ds["QGRAUP"].isel(Time=0).values,
    }


def get_w_field(time_index: int = 0) -> np.ndarray:
    """Return vertical velocity W at a time index."""
    ds = get_dataset(time_index)
    return ds["W"].isel(Time=0).values


def enrich_profile_with_vertical_levels(profile: list[dict]) -> list[dict]:
    """Add level_idx and pressure per time index to each profile point.

    For each point, finds the WRF model level whose geopotential height
    is closest to the target flight altitude, separately for the left and
    right time indices, and records the pressure at that level.
    """
    _scan_and_load()
    n_times = len(_datasets)
    z_list = [compute_geopotential_height(t).values for t in range(n_times)]
    p_list = [compute_pressure(t).values for t in range(n_times)]
    z_3d = np.stack(z_list, axis=0)
    p_3d = np.stack(p_list, axis=0)
    n_levels = z_3d.shape[1]

    for point in profile:
        lat_idx, lon_idx = find_nearest_grid_point(point["lat"], point["lon"])
        t_left = point.get("time_idx_left", 0)
        t_right = point.get("time_idx_right", 0)
        target_z = point["altitude_m"]

        z_left = z_3d[t_left, :, lat_idx, lon_idx]
        level_left = int(np.argmin(np.abs(z_left - target_z)))
        level_left = min(level_left, n_levels - 1)

        z_right = z_3d[t_right, :, lat_idx, lon_idx]
        level_right = int(np.argmin(np.abs(z_right - target_z)))
        level_right = min(level_right, n_levels - 1)

        point["level_idx_left"] = level_left
        point["level_idx_right"] = level_right
        point["pressure_left"] = float(p_3d[t_left, level_left, lat_idx, lon_idx])
        point["pressure_right"] = float(p_3d[t_right, level_right, lat_idx, lon_idx])

    return profile


def get_times_minutes() -> list[float]:
    """Return WRF timesteps as minutes from the first timestep."""
    _scan_and_load()
    base = _times[0]
    return [(t - base).total_seconds() / 60.0 for t in _times]


def get_temporal_coverage_minutes() -> float:
    """Return total temporal coverage of the WRF dataset in minutes."""
    minutes = get_times_minutes()
    return minutes[-1] - minutes[0]


def enrich_profile_with_temporal_info(
    profile: list[dict],
    flight_time_min: float,
) -> list[dict]:
    """Add temporal interpolation indices to each profile point.

    Each point gets time_idx_left, time_idx_right, time_frac (weight of right index).
    """
    times_min = get_times_minutes()
    n_times = len(times_min)

    for point in profile:
        frac = point["distance_km"] / profile[-1]["distance_km"] if profile[-1]["distance_km"] > 0 else 0.0
        point_time = frac * flight_time_min

        if n_times == 1:
            point["time_idx_left"] = 0
            point["time_idx_right"] = 0
            point["time_frac"] = 0.0
            continue

        if point_time <= times_min[0]:
            point["time_idx_left"] = 0
            point["time_idx_right"] = 0
            point["time_frac"] = 0.0
        elif point_time >= times_min[-1]:
            point["time_idx_left"] = n_times - 1
            point["time_idx_right"] = n_times - 1
            point["time_frac"] = 0.0
        else:
            for i in range(n_times - 1):
                if times_min[i] <= point_time <= times_min[i + 1]:
                    delta = times_min[i + 1] - times_min[i]
                    point["time_idx_left"] = i
                    point["time_idx_right"] = i + 1
                    point["time_frac"] = (point_time - times_min[i]) / delta if delta > 0 else 0.0
                    break

    return profile
