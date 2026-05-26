"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel


class CityResponse(BaseModel):
    name: str
    lat: float
    lon: float


class FieldInfo(BaseModel):
    id: str
    name: str
    description: str


class MapRequest(BaseModel):
    field: str
    time_index: int = 0


class MapResponse(BaseModel):
    image_base64: str
    title: str
    metadata: dict


class RouteRequest(BaseModel):
    origin: str
    destination: str
    cruise_level: str = "FL330"


class RouteInfo(BaseModel):
    origin: str
    destination: str
    distance_km: float
    flight_time_minutes: float
    cruise_level: str


class RiskSummary(BaseModel):
    icing: bool
    wind_shear: bool
    turbulence: bool
    convection: bool
    visibility: bool


class RouteResponse(BaseModel):
    image_base64: str
    route_map_base64: str | None = None
    route: RouteInfo
    risks: RiskSummary
