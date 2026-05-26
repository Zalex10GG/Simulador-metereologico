"""Plotting utilities: horizontal maps and vertical cross-sections."""

import base64
import functools
import io

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import numpy as np

from src import wrf_processing


def fig_to_base64(fig: plt.Figure) -> str:
    """Convert a Matplotlib figure to a base64 PNG string, ensuring it is closed."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"
    finally:
        plt.close(fig)


def _get_projection():
    """Return Cartopy projection for the WRF domain."""
    return ccrs.PlateCarree()


def plot_surface_wind(time_index: int = 0) -> tuple[str, str]:
    """Plot 10m wind speed with streamlines."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    speed = wrf_processing.compute_wind_speed_10m(time_index)
    ds = wrf_processing.get_dataset(time_index)
    u10 = ds["U10"].isel(Time=0).values
    v10 = ds["V10"].isel(Time=0).values

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, speed, levels=20, cmap="YlOrRd", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Wind Speed (m/s)", shrink=0.8)

        skip = (slice(None, None, 5), slice(None, None, 5))
        ax.streamplot(
            lon[skip], lat[skip], u10[skip], v10[skip],
            color="black", linewidth=0.8, density=1.5, arrowsize=0.8,
        )

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"10m Wind - {time_label}")

        return fig_to_base64(fig), f"10m Wind - {time_label}"
    except Exception:
        plt.close(fig)
        raise


def plot_surface_pressure(time_index: int = 0) -> tuple[str, str]:
    """Plot surface pressure."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    psfc = wrf_processing.compute_surface_pressure(time_index) / 100.0

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, psfc, levels=20, cmap="viridis", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Pressure (hPa)", shrink=0.8)

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"Surface Pressure - {time_label}")

        return fig_to_base64(fig), f"Surface Pressure - {time_label}"
    except Exception:
        plt.close(fig)
        raise


def plot_surface_temperature(time_index: int = 0) -> tuple[str, str]:
    """Plot 2m temperature in Celsius."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    t2 = wrf_processing.compute_temperature_2m(time_index)

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, t2, levels=20, cmap="RdYlBu_r", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Temperature (°C)", shrink=0.8)

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"2m Temperature - {time_label}")

        return fig_to_base64(fig), f"2m Temperature - {time_label}"
    except Exception:
        plt.close(fig)
        raise


def plot_mslp(time_index: int = 0) -> tuple[str, str]:
    """Plot Mean Sea Level Pressure."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    mslp = wrf_processing.compute_mslp(time_index) / 100.0

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, mslp, levels=20, cmap="viridis", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="MSLP (hPa)", shrink=0.8)

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"Mean Sea Level Pressure - {time_label}")

        return fig_to_base64(fig), f"Mean Sea Level Pressure - {time_label}"
    except Exception:
        plt.close(fig)
        raise


def plot_precipitation(time_index: int = 0) -> tuple[str, str]:
    """Plot accumulated precipitation."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    precip = wrf_processing.compute_precipitation(time_index)

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, precip, levels=20, cmap="Blues", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Accumulated Precipitation (mm)", shrink=0.8)

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"Accumulated Precipitation - {time_label}")

        return fig_to_base64(fig), f"Accumulated Precipitation - {time_label}"
    except Exception:
        plt.close(fig)
        raise


def plot_level_zt(pressure_level: float, time_index: int = 0) -> tuple[str, str]:
    """Plot geopotential height and temperature at a pressure level."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    z = wrf_processing.get_field_at_pressure_level("PH", pressure_level, time_index)
    t = wrf_processing.get_field_at_pressure_level("T", pressure_level, time_index)

    z_dam = z / 10.0  # Show in decameters (dam)
    t_c = t - 273.15

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, t_c, levels=20, cmap="RdYlBu_r", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Temperature (°C)", shrink=0.8)

        cs = ax.contour(lon, lat, z_dam, levels=15, colors="black", linewidths=0.8, transform=ccrs.PlateCarree())
        ax.clabel(cs, inline=True, fontsize=8, fmt="%.0f")

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"Geopotential Height (dam) & Temperature at {int(pressure_level)} hPa - {time_label}")

        return fig_to_base64(fig), f"Geopotential (dam) & Temperature at {int(pressure_level)} hPa - {time_label}"
    except Exception:
        plt.close(fig)
        raise


def plot_jet_stream(time_index: int = 0) -> tuple[str, str]:
    """Plot wind speed at 300 hPa (jet stream) with streamlines."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    u, v, speed = wrf_processing.get_wind_at_pressure_level(300, time_index)

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, speed, levels=20, cmap="YlOrRd", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Wind Speed (m/s)", shrink=0.8)

        skip = (slice(None, None, 5), slice(None, None, 5))
        ax.streamplot(
            lon[skip], lat[skip], u[skip], v[skip],
            color="black", linewidth=0.8, density=1.5, arrowsize=0.8,
        )

        times = wrf_processing.get_times()
        time_label = times[time_index] if time_index < len(times) else f"t={time_index}"
        ax.set_title(f"Jet Stream (300 hPa) - {time_label}")

        return fig_to_base64(fig), f"Jet Stream (300 hPa) - {time_label}"
    except Exception:
        plt.close(fig)
        raise


FIELD_PLOTTERS = {
    "surface_wind": plot_surface_wind,
    "surface_pressure": plot_surface_pressure,
    "mslp": plot_mslp,
    "surface_temperature": plot_surface_temperature,
    "surface_precipitation": plot_precipitation,
    "z_t_850": functools.partial(plot_level_zt, 850),
    "z_t_500": functools.partial(plot_level_zt, 500),
    "jet_300": plot_jet_stream,
}


def plot_route_map(
    route_points: list[dict],
    origin: str,
    destination: str,
    origin_coords: tuple[float, float],
    dest_coords: tuple[float, float],
) -> tuple[str, str]:
    """Plot the flight route on a geographical map."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()
    lats = [p["lat"] for p in route_points]
    lons = [p["lon"] for p in route_points]

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        ax.plot(lons, lats, "b-", linewidth=2, transform=ccrs.PlateCarree(), label="Flight path")
        ax.plot(lons[0], lats[0], "go", markersize=10, transform=ccrs.PlateCarree(), label=f"Origin: {origin}")
        ax.plot(lons[-1], lats[-1], "ro", markersize=10, transform=ccrs.PlateCarree(), label=f"Destination: {destination}")

        ax.legend(loc="upper right")
        ax.set_title(f"Flight Route: {origin} -> {destination}")

        return fig_to_base64(fig), f"Route Map: {origin} -> {destination}"
    except Exception:
        plt.close(fig)
        raise


def generate_map(field: str, time_index: int = 0) -> tuple[str, str]:
    """Generate a map for the given field and time index.

    Returns (image_base64, title).
    """
    if field not in FIELD_PLOTTERS:
        raise ValueError(f"Unknown field: {field}")

    n_times = len(wrf_processing.get_times())
    if time_index < 0 or time_index >= n_times:
        raise ValueError(f"Time index {time_index} out of range [0, {n_times - 1}]")

    return FIELD_PLOTTERS[field](time_index)


def plot_route_cross_section(
    route_points: list[dict],
    profile: list[dict],
    risks: dict,
    origin: str,
    destination: str,
    distance_km: float,
    flight_time_min: float,
) -> tuple[str, str]:
    """Plot vertical cross-section of route with risk shading.

    Args:
        route_points: list of dicts with lat, lon, distance_km
        profile: list of dicts with altitude_m, distance_km
        risks: dict with keys 'icing', 'wind_shear', 'turbulence',
               'convection', 'visibility', each a list of bools per route point
    """
    distances = np.array([p["distance_km"] for p in route_points])
    altitudes = np.array([p["altitude_m"] for p in profile])
    y_max = max(altitudes) * 1.15
    band_half = 500.0

    fig, ax = plt.subplots(figsize=(14, 7))
    try:
        risk_configs = [
            ("icing", "cyan", "Icing"),
            ("wind_shear", "orange", "Wind shear"),
            ("turbulence", "purple", "Turbulence"),
            ("convection", "red", "Convection"),
            ("visibility", "yellow", "Low visibility"),
        ]

        for key, color, label in risk_configs:
            mask = np.array(risks.get(key, [False] * len(distances)))
            if not mask.any():
                continue
            lower = np.maximum(0, altitudes - band_half)
            upper = altitudes + band_half
            ax.fill_between(
                distances, lower, upper,
                where=mask, alpha=0.35, color=color, label=label, step=None,
            )

        ax.plot(distances, altitudes, "b-", linewidth=2, label="Flight profile")

        ax.set_xlabel("Distance (km)")
        ax.set_ylabel("Altitude (m)")
        ax.set_title(
            f"Route: {origin} -> {destination}\n"
            f"Distance: {distance_km:.0f} km | Flight time: {flight_time_min:.1f} min"
        )
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, y_max)

        return fig_to_base64(fig), f"Route: {origin} -> {destination}"
    except Exception:
        plt.close(fig)
        raise


def plot_sounding(profile: dict, lat: float, lon: float, time_label: str) -> tuple[str, str]:
    """Plot Skew-T log-P and Hodograph for a vertical profile.

    Returns (image_base64, title).
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from metpy.plots import SkewT, Hodograph
    from metpy.units import units

    p = (profile["pressure"] / 100.0) * units.hPa
    t = (profile["temperature"] - 273.15) * units.degC
    td = (profile["dewpoint"] - 273.15) * units.degC
    u = profile["u_wind"] * units('m/s')
    v = profile["v_wind"] * units('m/s')

    fig = plt.figure(figsize=(14, 9))
    try:
        gs = GridSpec(3, 3, figure=fig, wspace=0.3, hspace=0.3)

        # 1. Skew-T Log-P
        skew = SkewT(fig, subplot=gs[:, :2])
        skew.plot(p, t, 'r', linewidth=2, label='Temperatura')
        skew.plot(p, td, 'g', linewidth=2, label='Temperatura de Rocío')

        # Plot wind barbs (only every 2nd level to avoid clutter)
        skip = slice(None, None, 2)
        skew.plot_barbs(p[skip], u[skip], v[skip], xloc=1.05)

        skew.ax.set_ylim(1000, 100)
        skew.ax.set_xlim(-40, 40)

        # Add thermodynamic reference lines
        skew.plot_dry_adiabats(alpha=0.25, color='orange')
        skew.plot_moist_adiabats(alpha=0.25, color='green')
        skew.plot_mixing_lines(alpha=0.25, color='blue')

        skew.ax.set_xlabel('Temperatura (°C)')
        skew.ax.set_ylabel('Presión (hPa)')
        skew.ax.legend(loc='upper left')

        # 2. Hodograph (right-top)
        ax_hodo = fig.add_subplot(gs[0, 2])
        hodo_range = max(float(np.max(np.abs(profile["u_wind"]))), float(np.max(np.abs(profile["v_wind"]))), 20.0)
        h = Hodograph(ax_hodo, component_range=hodo_range)
        h.add_grid(increment=10, color='gray', linestyle='--', alpha=0.5)

        # Plot hodograph line colored by pressure height
        h.plot_colormapped(u, v, profile["pressure"] / 100.0, cmap='jet')
        ax_hodo.set_title('Odógrafa (m/s)', fontsize=10)

        # Title and info
        title = f"Sondeo Atmosférico - Lat: {lat:.2f}, Lon: {lon:.2f} - {time_label}"
        fig.suptitle(title, fontsize=14, fontweight='bold')

        return fig_to_base64(fig), title
    except Exception:
        plt.close(fig)
        raise

