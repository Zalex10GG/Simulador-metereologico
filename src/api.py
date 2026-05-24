"""FastAPI application for meteorological route simulator."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src import cities, plotting, risk, routing, schemas, wrf_processing
from src.config import FRONTEND_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-scan and load datasets at startup
    try:
        wrf_processing._scan_and_load()
        print(f"Preloaded {len(wrf_processing._datasets)} WRF snapshot files.")
    except Exception as e:
        print(f"Error loading datasets on startup: {e}")
    yield
    wrf_processing._datasets.clear()
    wrf_processing._times.clear()


app = FastAPI(title="Meteorological Route Simulator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FIELDS = {
    "surface_wind": {"id": "surface_wind", "name": "10m Wind", "description": "Wind speed and direction at 10m"},
    "surface_pressure": {"id": "surface_pressure", "name": "Surface Pressure", "description": "Surface pressure (PSFC)"},
    "surface_temperature": {"id": "surface_temperature", "name": "2m Temperature", "description": "Temperature at 2m in Celsius"},
    "surface_precipitation": {"id": "surface_precipitation", "name": "Accumulated Precipitation", "description": "RAINC + RAINNC"},
    "z_t_850": {"id": "z_t_850", "name": "850 hPa", "description": "Geopotential height and temperature at 850 hPa"},
    "z_t_500": {"id": "z_t_500", "name": "500 hPa", "description": "Geopotential height and temperature at 500 hPa"},
    "jet_300": {"id": "jet_300", "name": "Jet Stream (300 hPa)", "description": "Wind speed at 300 hPa"},
}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/cities", response_model=list[schemas.CityResponse])
async def get_cities():
    return cities.get_cities()


@app.get("/api/fields", response_model=list[schemas.FieldInfo])
async def get_fields():
    return list(FIELDS.values())


@app.get("/api/times")
async def get_times():
    times = wrf_processing.get_times()
    return [{"index": i, "time": t} for i, t in enumerate(times)]


@app.post("/api/map", response_model=schemas.MapResponse)
async def generate_map(req: schemas.MapRequest):
    if req.field not in FIELDS:
        raise HTTPException(status_code=400, detail=f"Unknown field: {req.field}. Available: {list(FIELDS.keys())}")

    n_times = len(wrf_processing.get_times())
    if req.time_index < 0 or req.time_index >= n_times:
        raise HTTPException(
            status_code=400,
            detail=f"Time index {req.time_index} out of range [0, {n_times - 1}]",
        )

    try:
        image_base64, title = plotting.generate_map(req.field, req.time_index)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating map: {str(e)}")

    return schemas.MapResponse(
        image_base64=image_base64,
        title=title,
        metadata={"time_index": req.time_index, "field": req.field},
    )


@app.post("/api/route", response_model=schemas.RouteResponse)
async def simulate_route(req: schemas.RouteRequest):
    if req.origin.lower() == req.destination.lower():
        raise HTTPException(status_code=400, detail="Origin and destination must be different cities")

    origin_city = cities.get_city(req.origin)
    if origin_city is None:
        raise HTTPException(status_code=400, detail=f"Unknown origin city: {req.origin}")

    dest_city = cities.get_city(req.destination)
    if dest_city is None:
        raise HTTPException(status_code=400, detail=f"Unknown destination city: {req.destination}")

    domain_bounds = wrf_processing.get_domain_bounds()

    if not wrf_processing.is_in_domain(origin_city["lat"], origin_city["lon"]):
        raise HTTPException(
            status_code=400,
            detail=f"Origin city {req.origin} ({origin_city['lat']:.2f}, {origin_city['lon']:.2f}) is outside WRF domain",
        )

    if not wrf_processing.is_in_domain(dest_city["lat"], dest_city["lon"]):
        raise HTTPException(
            status_code=400,
            detail=f"Destination city {req.destination} ({dest_city['lat']:.2f}, {dest_city['lon']:.2f}) is outside WRF domain",
        )

    route_points = routing.great_circle_points(
        origin_city["lat"], origin_city["lon"],
        dest_city["lat"], dest_city["lon"],
    )

    is_valid, error_msg = routing.validate_route_in_domain(route_points, domain_bounds)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Route {req.origin}-{req.destination} is outside WRF domain: {error_msg}",
        )

    total_distance_km = routing.haversine_km(
        origin_city["lat"], origin_city["lon"],
        dest_city["lat"], dest_city["lon"],
    )
    flight_time_min = routing.compute_flight_time_minutes(total_distance_km)

    temporal_coverage = wrf_processing.get_temporal_coverage_minutes()
    if flight_time_min > temporal_coverage:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Flight time ({flight_time_min:.1f} min) exceeds WRF temporal coverage "
                f"({temporal_coverage:.0f} min). Cannot simulate this route."
            ),
        )

    profile = routing.compute_flight_profile(route_points, total_distance_km)
    profile = wrf_processing.enrich_profile_with_temporal_info(profile, flight_time_min)
    profile = wrf_processing.enrich_profile_with_vertical_levels(profile)

    risks = risk.compute_all_risks(profile)

    try:
        image_base64, title = plotting.plot_route_cross_section(
            route_points,
            profile,
            risks,
            req.origin,
            req.destination,
            total_distance_km,
            flight_time_min,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating route plot: {str(e)}")

    return schemas.RouteResponse(
        image_base64=image_base64,
        route=schemas.RouteInfo(
            origin=req.origin,
            destination=req.destination,
            distance_km=round(total_distance_km, 1),
            flight_time_minutes=round(flight_time_min, 1),
            cruise_level="FL330",
        ),
        risks=schemas.RiskSummary(
            icing=any(risks["icing"]),
            wind_shear=any(risks["wind_shear"]),
            convection_visibility=any(risks["convection_visibility"]),
        ),
    )


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
