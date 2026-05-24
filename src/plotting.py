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
    """Plot 10m wind speed with direction arrows."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    speed = wrf_processing.compute_wind_speed_10m(time_index)
    ds = wrf_processing.get_dataset(time_index)
    u10 = ds["U10"].isel(Time=0).values
    v10 = ds["V10"].isel(Time=0).values

    # Normalize components for direction-only arrows
    norm10 = np.sqrt(u10**2 + v10**2)
    norm10[norm10 == 0] = 1.0
    u10_dir = u10 / norm10
    v10_dir = v10 / norm10

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, speed, levels=20, cmap="YlOrRd", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Wind Speed (m/s)", shrink=0.8)

        skip = (slice(None, None, 20), slice(None, None, 20))
        ax.quiver(
            lon[skip], lat[skip], u10_dir[skip], v10_dir[skip],
            color="black", scale=50, width=0.003, transform=ccrs.PlateCarree(),
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
    """Plot wind speed at 300 hPa (jet stream)."""
    proj = _get_projection()
    lat, lon = wrf_processing.get_coordinates()

    u, v, speed = wrf_processing.get_wind_at_pressure_level(300, time_index)

    # Normalize components for direction-only arrows
    norm = np.sqrt(u**2 + v**2)
    norm[norm == 0] = 1.0
    u_dir = u / norm
    v_dir = v / norm

    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": proj})
    try:
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=proj)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        cf = ax.contourf(lon, lat, speed, levels=20, cmap="YlOrRd", transform=ccrs.PlateCarree())
        fig.colorbar(cf, ax=ax, label="Wind Speed (m/s)", shrink=0.8)

        skip = (slice(None, None, 20), slice(None, None, 20))
        ax.quiver(
            lon[skip], lat[skip], u_dir[skip], v_dir[skip],
            color="black", scale=50, width=0.003, transform=ccrs.PlateCarree(),
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
    "surface_temperature": plot_surface_temperature,
    "surface_precipitation": plot_precipitation,
    "z_t_850": functools.partial(plot_level_zt, 850),
    "z_t_500": functools.partial(plot_level_zt, 500),
    "jet_300": plot_jet_stream,
}


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
        risks: dict with keys 'icing', 'wind_shear', 'convection_visibility',
               each a list of bools per route point
    """
    distances = [p["distance_km"] for p in route_points]
    altitudes = [p["altitude_m"] for p in profile]

    fig, ax = plt.subplots(figsize=(14, 7))
    try:
        icing_mask = risks.get("icing", [False] * len(distances))
        shear_mask = risks.get("wind_shear", [False] * len(distances))
        conv_mask = risks.get("convection_visibility", [False] * len(distances))

        if any(icing_mask):
            ax.fill_between(
                distances, 0, max(altitudes) * 1.1,
                where=icing_mask, alpha=0.3, color="cyan", label="Icing risk",
            )
        if any(shear_mask):
            ax.fill_between(
                distances, 0, max(altitudes) * 1.1,
                where=shear_mask, alpha=0.3, color="orange", label="Wind shear",
            )
        if any(conv_mask):
            ax.fill_between(
                distances, 0, max(altitudes) * 1.1,
                where=conv_mask, alpha=0.3, color="red", label="Convection/Visibility",
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
        ax.set_ylim(0, max(altitudes) * 1.15)

        return fig_to_base64(fig), f"Route: {origin} -> {destination}"
    except Exception:
        plt.close(fig)
        raise
