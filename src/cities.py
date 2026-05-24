"""European cities database for route simulation."""

CITIES = {
    "Madrid": {"lat": 40.4168, "lon": -3.7038},
    "Barcelona": {"lat": 41.3874, "lon": 2.1686},
    "Lisboa": {"lat": 38.7223, "lon": -9.1393},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Londres": {"lat": 51.5074, "lon": -0.1278},
    "Dublin": {"lat": 53.3498, "lon": -6.2603},
    "Roma": {"lat": 41.9028, "lon": 12.4964},
    "Milan": {"lat": 45.4642, "lon": 9.1900},
    "Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Amsterdam": {"lat": 52.3676, "lon": 4.9041},
    "Bruselas": {"lat": 50.8503, "lon": 4.3517},
    "Viena": {"lat": 48.2082, "lon": 16.3738},
    "Zurich": {"lat": 47.3769, "lon": 8.5417},
    "Praga": {"lat": 50.0755, "lon": 14.4378},
    "Varsovia": {"lat": 52.2297, "lon": 21.0122},
    "Copenhague": {"lat": 55.6761, "lon": 12.5683},
    "Oslo": {"lat": 59.9139, "lon": 10.7522},
    "Estocolmo": {"lat": 59.3293, "lon": 18.0686},
    "Helsinki": {"lat": 60.1699, "lon": 24.9384},
    "Atenas": {"lat": 37.9838, "lon": 23.7275},
}


def get_cities() -> list[dict]:
    """Return sorted list of cities with name, lat, lon."""
    return [
        {"name": name, "lat": info["lat"], "lon": info["lon"]}
        for name, info in sorted(CITIES.items())
    ]


def get_city(name: str) -> dict | None:
    """Get city coordinates by name (case-insensitive)."""
    for city_name, info in CITIES.items():
        if city_name.lower() == name.lower():
            return {"name": city_name, "lat": info["lat"], "lon": info["lon"]}
    return None
