"""Tests for config module."""

from src.config import (
    CRUISE_LEVELS,
    CRUISE_SPEED_KMH,
    ICING_HYDROMETEOR_THRESHOLD,
    ROUTE_NUM_POINTS,
)


def test_cruise_levels():
    assert "FL240" in CRUISE_LEVELS
    assert "FL330" in CRUISE_LEVELS
    assert "FL380" in CRUISE_LEVELS
    assert CRUISE_LEVELS["FL330"] == 10058.4


def test_cruise_speed():
    assert CRUISE_SPEED_KMH == 850.0


def test_route_num_points():
    assert ROUTE_NUM_POINTS >= 50


def test_icing_threshold():
    assert ICING_HYDROMETEOR_THRESHOLD == 1e-6
