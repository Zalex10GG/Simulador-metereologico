"""Tests for routing module."""

from src.routing import great_circle_points, haversine_km, compute_flight_time_minutes


def test_haversine_madrid_paris():
    dist = haversine_km(40.4168, -3.7038, 48.8566, 2.3522)
    assert 1000 < dist < 1100


def test_haversine_self():
    dist = haversine_km(40.0, -3.0, 40.0, -3.0)
    assert dist == 0.0


def test_great_circle_points_count():
    points = great_circle_points(40.4168, -3.7038, 48.8566, 2.3522, num_points=50)
    assert len(points) == 50


def test_great_circle_first_point():
    points = great_circle_points(40.4168, -3.7038, 48.8566, 2.3522, num_points=100)
    assert abs(points[0]["lat"] - 40.4168) < 0.01
    assert abs(points[0]["lon"] - (-3.7038)) < 0.01
    assert points[0]["distance_km"] == 0.0


def test_great_circle_last_point():
    points = great_circle_points(40.4168, -3.7038, 48.8566, 2.3522, num_points=100)
    assert abs(points[-1]["lat"] - 48.8566) < 0.01
    assert abs(points[-1]["lon"] - 2.3522) < 0.01


def test_flight_time():
    time = compute_flight_time_minutes(1000.0)
    assert abs(time - 70.588) < 0.1
