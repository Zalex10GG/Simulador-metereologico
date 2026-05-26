"""Configuration constants for the meteorological simulator."""

from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"

# WRF dataset
WRF_FILE_PATTERN = "wrfout_*.nc"

# Physical constants
G = 9.81  # m/s^2, gravitational acceleration
P0 = 100000.0  # Pa, reference pressure
R_CP = 2.0 / 7.0  # R/Cp ≈ 0.2857 for dry air
R_DRY = 287.058  # J/(kg·K), specific gas constant for dry air
GAMMA = 0.0065  # K/m, standard temperature lapse rate for MSLP reduction

# Flight parameters
CRUISE_SPEED_KMH = 850.0
CRUISE_LEVEL_FT = 33000  # FL330
CRUISE_LEVEL_M = 10058.4  # 33000 ft to meters
CRUISE_LEVELS = {
    "FL240": 7315.2,
    "FL330": 10058.4,
    "FL380": 11582.4,
}

# Route sampling
ROUTE_NUM_POINTS = 100

# Risk thresholds
ICING_HYDROMETEOR_THRESHOLD = 1e-6  # kg/kg
WIND_SHEAR_VERTICAL_THRESHOLD = 0.005  # s^-1
WIND_SHEAR_HORIZONTAL_THRESHOLD = 0.01  # s^-1
CONVECTION_PRECIP_THRESHOLD = 0.001  # kg/m^2/s approx

VISIBILITY_QCLOUD_THRESHOLD = 1e-5  # kg/kg, low-level cloud as visibility proxy
