"""
Ephemeris Module - High-precision planetary position calculations.

This module provides geocentric and heliocentric positions of celestial bodies
using the Swiss Ephemeris library. It supports both SWIEPH (Swiss Ephemeris files)
and MOSEPH (Moshier algorithm) methods.

Precision estimates:
- SWIEPH with .se1 files: ~0.001 arcsec for planets
- MOSEPH (Moshier): ~0.1 arcsec for planets
"""

import os
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import swisseph as swe

from data.symbols import (
    ZODIAC_SIGNS,
    get_zodiac_sign,
    get_sign_degree,
    longitude_to_dms,
    longitude_to_zodiacal,
)


class CelestialBody(IntEnum):
    """Swiss Ephemeris body constants."""

    SUN = swe.SUN
    MOON = swe.MOON
    MERCURY = swe.MERCURY
    VENUS = swe.VENUS
    MARS = swe.MARS
    JUPITER = swe.JUPITER
    SATURN = swe.SATURN
    URANUS = swe.URANUS
    NEPTUNE = swe.NEPTUNE
    PLUTO = swe.PLUTO
    MEAN_NODE = swe.MEAN_NODE
    TRUE_NODE = swe.TRUE_NODE
    CHIRON = swe.CHIRON
    MEAN_APOGEE = swe.MEAN_APOG  # Mean Lilith


# Mapping from string names to Swiss Ephemeris constants
BODY_MAP = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "mean_node": swe.MEAN_NODE,
    "true_node": swe.TRUE_NODE,
    "chiron": swe.CHIRON,
    "mean_apogee": swe.MEAN_APOG,
}

# Reverse mapping
BODY_NAMES = {v: k for k, v in BODY_MAP.items()}


@dataclass
class PlanetPosition:
    """Position data for a celestial body."""

    body: str
    longitude_decimal: float  # 0-360
    longitude_dms: str  # "123°45'67.89\""
    longitude_zodiacal: str  # "15°23'45\" Leo"
    latitude_decimal: float  # degrees from ecliptic
    distance_au: float  # distance in AU
    speed_longitude: float  # degrees per day
    speed_latitude: float  # degrees per day
    speed_distance: float  # AU per day
    is_retrograde: bool
    zodiac_sign: str
    zodiac_degree: int  # 0-29 within sign
    calculation_flag: str  # 'SWIEPH' or 'MOSEPH'
    precision_estimate_arcsec: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "body": self.body,
            "longitude_decimal": self.longitude_decimal,
            "longitude_dms": self.longitude_dms,
            "longitude_zodiacal": self.longitude_zodiacal,
            "latitude_decimal": self.latitude_decimal,
            "distance_au": self.distance_au,
            "speed_longitude": self.speed_longitude,
            "speed_latitude": self.speed_latitude,
            "speed_distance": self.speed_distance,
            "is_retrograde": self.is_retrograde,
            "zodiac_sign": self.zodiac_sign,
            "zodiac_degree": self.zodiac_degree,
            "calculation_flag": self.calculation_flag,
            "precision_estimate_arcsec": self.precision_estimate_arcsec,
        }


class EphemerisEngine:
    """
    High-precision ephemeris calculation engine.

    Uses Swiss Ephemeris for planetary position calculations with
    automatic fallback from SWIEPH to MOSEPH if data files are not available.
    """

    # Standard celestial bodies for natal charts
    STANDARD_BODIES = [
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
        "mean_node",
        "true_node",
        "chiron",
        "mean_apogee",
    ]

    # Precision estimates (arcseconds)
    PRECISION_SWIEPH = 0.001
    PRECISION_MOSEPH = 0.1

    def __init__(self, ephemeris_path: Optional[str] = None):
        """
        Initialize the ephemeris engine.

        Args:
            ephemeris_path: Path to Swiss Ephemeris data files (.se1)
                           If None, will try default locations then fall back to MOSEPH
        """
        self._ephemeris_path = ephemeris_path
        self._using_swieph = False

        # Try to set ephemeris path
        self._init_ephemeris(ephemeris_path)

    def _init_ephemeris(self, path: Optional[str] = None):
        """Initialize ephemeris with given path or search defaults."""
        search_paths = []

        if path:
            search_paths.append(path)

        # Add common default locations
        search_paths.extend(
            [
                "data/ephemeris",
                "./ephe",
                "/usr/share/sweph/ephe",
                "/usr/local/share/sweph/ephe",
                os.path.expanduser("~/.sweph/ephe"),
            ]
        )

        for eph_path in search_paths:
            if os.path.isdir(eph_path):
                # Check if there are .se1 files
                has_se1 = any(f.endswith(".se1") for f in os.listdir(eph_path))
                if has_se1:
                    swe.set_ephe_path(eph_path)
                    self._ephemeris_path = eph_path
                    self._using_swieph = True
                    return

        # No ephemeris files found, will use MOSEPH
        self._using_swieph = False

    def get_position(
        self,
        body: str,
        jd_tt: float,
        flags: Optional[int] = None,
    ) -> PlanetPosition:
        """
        Calculate position of a celestial body.

        Args:
            body: Body name (e.g., 'sun', 'moon', 'mars')
            jd_tt: Julian Day in Terrestrial Time
            flags: Swiss Ephemeris flags (optional, will choose best available)

        Returns:
            PlanetPosition with all position data
        """
        if body not in BODY_MAP:
            raise ValueError(f"Unknown body: {body}. Valid bodies: {list(BODY_MAP.keys())}")

        body_id = BODY_MAP[body]

        # Determine flags
        if flags is None:
            if self._using_swieph:
                flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            else:
                flags = swe.FLG_MOSEPH | swe.FLG_SPEED

        # Calculate position
        try:
            result, ret_flags = swe.calc_ut(jd_tt, body_id, flags)
        except Exception as e:
            # Try MOSEPH as fallback
            flags = swe.FLG_MOSEPH | swe.FLG_SPEED
            result, ret_flags = swe.calc_ut(jd_tt, body_id, flags)

        # Unpack results
        # result = [longitude, latitude, distance, speed_lon, speed_lat, speed_dist]
        longitude = result[0]
        latitude = result[1]
        distance = result[2]
        speed_lon = result[3]
        speed_lat = result[4]
        speed_dist = result[5]

        # Determine calculation method from return flags
        if ret_flags & swe.FLG_SWIEPH:
            calc_flag = "SWIEPH"
            precision = self.PRECISION_SWIEPH
        else:
            calc_flag = "MOSEPH"
            precision = self.PRECISION_MOSEPH

        # Moon has lower precision due to complex perturbations
        if body == "moon":
            precision *= 10

        return PlanetPosition(
            body=body,
            longitude_decimal=longitude,
            longitude_dms=longitude_to_dms(longitude),
            longitude_zodiacal=longitude_to_zodiacal(longitude),
            latitude_decimal=latitude,
            distance_au=distance,
            speed_longitude=speed_lon,
            speed_latitude=speed_lat,
            speed_distance=speed_dist,
            is_retrograde=speed_lon < 0,
            zodiac_sign=get_zodiac_sign(longitude),
            zodiac_degree=get_sign_degree(longitude),
            calculation_flag=calc_flag,
            precision_estimate_arcsec=precision,
        )

    def get_all_positions(
        self, jd_tt: float, bodies: Optional[list] = None
    ) -> dict[str, PlanetPosition]:
        """
        Calculate positions for multiple bodies.

        Args:
            jd_tt: Julian Day in Terrestrial Time
            bodies: List of body names (default: STANDARD_BODIES)

        Returns:
            Dictionary mapping body names to PlanetPosition objects
        """
        if bodies is None:
            bodies = self.STANDARD_BODIES

        positions = {}
        for body in bodies:
            try:
                positions[body] = self.get_position(body, jd_tt)
            except Exception as e:
                # Skip bodies that can't be calculated (e.g., Chiron before discovery)
                pass

        return positions

    def get_sun_moon_positions(self, jd_tt: float) -> tuple[PlanetPosition, PlanetPosition]:
        """Get Sun and Moon positions (commonly needed together)."""
        sun = self.get_position("sun", jd_tt)
        moon = self.get_position("moon", jd_tt)
        return sun, moon

    def get_lunar_phase(self, jd_tt: float) -> dict:
        """
        Calculate lunar phase information.

        Args:
            jd_tt: Julian Day in TT

        Returns:
            Dictionary with phase angle, illumination, phase name, etc.
        """
        sun = self.get_position("sun", jd_tt)
        moon = self.get_position("moon", jd_tt)

        # Phase angle (Moon - Sun longitude)
        phase_angle = (moon.longitude_decimal - sun.longitude_decimal) % 360

        # Illumination fraction (approximate)
        illumination = (1 - abs(180 - phase_angle) / 180) * 100

        # Phase name
        if phase_angle < 22.5:
            phase_name = "New Moon"
        elif phase_angle < 67.5:
            phase_name = "Waxing Crescent"
        elif phase_angle < 112.5:
            phase_name = "First Quarter"
        elif phase_angle < 157.5:
            phase_name = "Waxing Gibbous"
        elif phase_angle < 202.5:
            phase_name = "Full Moon"
        elif phase_angle < 247.5:
            phase_name = "Waning Gibbous"
        elif phase_angle < 292.5:
            phase_name = "Last Quarter"
        elif phase_angle < 337.5:
            phase_name = "Waning Crescent"
        else:
            phase_name = "New Moon"

        return {
            "phase_angle": phase_angle,
            "illumination_percent": illumination,
            "phase_name": phase_name,
            "sun_longitude": sun.longitude_decimal,
            "moon_longitude": moon.longitude_decimal,
            "is_waxing": phase_angle < 180,
        }

    def get_ecliptic_obliquity(self, jd_tt: float) -> dict:
        """
        Get the obliquity of the ecliptic.

        Args:
            jd_tt: Julian Day in TT

        Returns:
            Dictionary with mean and true obliquity
        """
        # Get nutation and obliquity
        nut = swe.calc_ut(jd_tt, swe.ECL_NUT, 0)

        # nut[0] = nutation in longitude
        # nut[1] = nutation in obliquity
        # nut[2] = mean obliquity
        # nut[3] = true obliquity

        return {
            "nutation_longitude": nut[0][0],
            "nutation_obliquity": nut[0][1],
            "mean_obliquity": nut[0][2],
            "true_obliquity": nut[0][3] if len(nut[0]) > 3 else nut[0][2] + nut[0][1],
        }

    @property
    def calculation_method(self) -> str:
        """Return the current calculation method."""
        return "SWIEPH" if self._using_swieph else "MOSEPH"

    @property
    def ephemeris_path(self) -> Optional[str]:
        """Return the ephemeris file path if using SWIEPH."""
        return self._ephemeris_path if self._using_swieph else None


# Module-level convenience instance
_engine = EphemerisEngine()


def get_position(body: str, jd_tt: float) -> PlanetPosition:
    """Calculate position of a celestial body."""
    return _engine.get_position(body, jd_tt)


def get_all_positions(jd_tt: float, bodies: Optional[list] = None) -> dict:
    """Calculate positions for multiple bodies."""
    return _engine.get_all_positions(jd_tt, bodies)


def get_lunar_phase(jd_tt: float) -> dict:
    """Calculate lunar phase information."""
    return _engine.get_lunar_phase(jd_tt)


def set_ephemeris_path(path: str):
    """Set the path to Swiss Ephemeris data files."""
    global _engine
    _engine = EphemerisEngine(path)
