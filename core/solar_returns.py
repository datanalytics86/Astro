"""
Solar Returns Module - Annual solar return chart calculations.

A solar return occurs when the transiting Sun returns to its exact
natal position. This happens approximately once per year (within
a day of the birthday) and the chart cast for this moment is used
for annual forecasting.

Features:
- High-precision solar return time calculation
- Relocated solar returns (for different locations)
- Multiple year calculation
- Comparison with natal chart
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from core.ephemeris import get_position, get_all_positions, EphemerisEngine
from core.houses import calculate_houses, HouseData
from core.aspects import find_all_aspects
from core.time_engine import datetime_to_jd, jd_to_datetime, local_to_ut


@dataclass
class SolarReturnData:
    """Complete solar return chart data."""

    year: int
    exact_datetime_utc: datetime
    jd_exact: float
    sun_longitude: float
    natal_sun_longitude: float
    precision_achieved: float  # degrees

    # Chart data
    positions: dict
    houses: HouseData
    aspects: list

    # Location used
    latitude: float
    longitude: float
    location_name: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "year": self.year,
            "exact_datetime_utc": self.exact_datetime_utc.isoformat(),
            "jd_exact": self.jd_exact,
            "sun_longitude": self.sun_longitude,
            "natal_sun_longitude": self.natal_sun_longitude,
            "precision_degrees": self.precision_achieved,
            "positions": {k: v.to_dict() if hasattr(v, 'to_dict') else v
                         for k, v in self.positions.items()},
            "houses": self.houses.to_dict() if hasattr(self.houses, 'to_dict') else self.houses,
            "aspects": [a.to_dict() if hasattr(a, 'to_dict') else a for a in self.aspects],
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
        }


class SolarReturnCalculator:
    """
    Calculate solar return charts with high precision.

    Uses bisection algorithm to find the exact moment when the
    transiting Sun returns to its natal longitude.
    """

    # Default precision: ~0.36 arcseconds
    DEFAULT_PRECISION = 0.0001  # degrees

    def __init__(self, precision_degrees: float = None):
        """
        Initialize calculator.

        Args:
            precision_degrees: Target precision in degrees
        """
        self.precision = precision_degrees or self.DEFAULT_PRECISION
        self.ephemeris = EphemerisEngine()

    def find_solar_return(
        self,
        natal_sun_longitude: float,
        year: int,
        natal_month: int = 1,
        natal_day: int = 1,
    ) -> tuple[float, float]:
        """
        Find the exact Julian Day of solar return for a given year.

        Args:
            natal_sun_longitude: Natal Sun longitude (0-360)
            year: Year for solar return
            natal_month: Birth month (for search window)
            natal_day: Birth day (for search window)

        Returns:
            Tuple of (julian_day, achieved_precision)
        """
        # Start search around birthday
        # Solar return can be up to ~1 day before or after birthday
        search_start = datetime(year, natal_month, natal_day) - timedelta(days=2)
        search_end = datetime(year, natal_month, natal_day) + timedelta(days=2)

        jd_start = datetime_to_jd(search_start)
        jd_end = datetime_to_jd(search_end)

        # Find where Sun crosses natal longitude using bisection
        return self._bisect_solar_return(natal_sun_longitude, jd_start, jd_end)

    def _bisect_solar_return(
        self,
        target_longitude: float,
        jd_start: float,
        jd_end: float,
    ) -> tuple[float, float]:
        """
        Use bisection to find exact solar return time.

        Args:
            target_longitude: Target Sun longitude
            jd_start: Start of search window (JD)
            jd_end: End of search window (JD)

        Returns:
            Tuple of (julian_day, precision_achieved)
        """
        # Get initial positions
        sun_start = get_position("sun", jd_start).longitude_decimal
        sun_end = get_position("sun", jd_end).longitude_decimal

        # Calculate signed distances from target
        dist_start = self._signed_distance(sun_start, target_longitude)
        dist_end = self._signed_distance(sun_end, target_longitude)

        # Ensure we bracket the target
        if dist_start * dist_end > 0:
            # Not bracketing, expand search
            jd_start -= 1
            jd_end += 1
            sun_start = get_position("sun", jd_start).longitude_decimal
            sun_end = get_position("sun", jd_end).longitude_decimal
            dist_start = self._signed_distance(sun_start, target_longitude)
            dist_end = self._signed_distance(sun_end, target_longitude)

        # Bisection loop
        iterations = 0
        max_iterations = 60

        while iterations < max_iterations:
            jd_mid = (jd_start + jd_end) / 2
            sun_mid = get_position("sun", jd_mid).longitude_decimal
            dist_mid = self._signed_distance(sun_mid, target_longitude)

            # Check precision
            if abs(dist_mid) < self.precision:
                return jd_mid, abs(dist_mid)

            # Update bracket
            if dist_mid * dist_start < 0:
                jd_end = jd_mid
                dist_end = dist_mid
            else:
                jd_start = jd_mid
                dist_start = dist_mid

            iterations += 1

        # Return best estimate
        jd_result = (jd_start + jd_end) / 2
        sun_result = get_position("sun", jd_result).longitude_decimal
        precision = abs(self._signed_distance(sun_result, target_longitude))

        return jd_result, precision

    def _signed_distance(self, current: float, target: float) -> float:
        """Calculate signed angular distance."""
        diff = current - target
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return diff

    def calculate_solar_return(
        self,
        natal_sun_longitude: float,
        natal_date: datetime,
        year: int,
        latitude: float,
        longitude: float,
        location_name: str = "Solar Return Location",
        house_system: str = "P",
    ) -> SolarReturnData:
        """
        Calculate complete solar return chart.

        Args:
            natal_sun_longitude: Natal Sun longitude
            natal_date: Birth date (for search window)
            year: Year for solar return
            latitude: Location latitude for chart
            longitude: Location longitude for chart
            location_name: Name of location
            house_system: House system to use

        Returns:
            SolarReturnData with complete chart
        """
        # Find exact return time
        jd_exact, precision = self.find_solar_return(
            natal_sun_longitude,
            year,
            natal_date.month,
            natal_date.day,
        )

        exact_dt = jd_to_datetime(jd_exact)

        # Calculate planetary positions
        positions = get_all_positions(jd_exact)

        # Calculate houses for specified location
        houses = calculate_houses(jd_exact, latitude, longitude, house_system)

        # Add angles to positions for aspect calculation
        positions_with_angles = dict(positions)
        positions_with_angles["ascendant"] = {"longitude_decimal": houses.ascendant}
        positions_with_angles["mc"] = {"longitude_decimal": houses.mc}

        # Calculate aspects
        aspects = find_all_aspects(positions_with_angles, jd_exact)

        return SolarReturnData(
            year=year,
            exact_datetime_utc=exact_dt,
            jd_exact=jd_exact,
            sun_longitude=positions["sun"].longitude_decimal,
            natal_sun_longitude=natal_sun_longitude,
            precision_achieved=precision,
            positions=positions,
            houses=houses,
            aspects=aspects,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
        )

    def calculate_multiple_returns(
        self,
        natal_sun_longitude: float,
        natal_date: datetime,
        start_year: int,
        end_year: int,
        latitude: float,
        longitude: float,
        location_name: str = "Location",
        house_system: str = "P",
    ) -> list[SolarReturnData]:
        """
        Calculate solar returns for a range of years.

        Args:
            natal_sun_longitude: Natal Sun longitude
            natal_date: Birth date
            start_year: First year to calculate
            end_year: Last year to calculate
            latitude: Location latitude
            longitude: Location longitude
            location_name: Name of location
            house_system: House system

        Returns:
            List of SolarReturnData for each year
        """
        returns = []

        for year in range(start_year, end_year + 1):
            sr = self.calculate_solar_return(
                natal_sun_longitude,
                natal_date,
                year,
                latitude,
                longitude,
                location_name,
                house_system,
            )
            returns.append(sr)

        return returns

    def relocated_solar_return(
        self,
        natal_sun_longitude: float,
        natal_date: datetime,
        year: int,
        locations: list[dict],
        house_system: str = "P",
    ) -> list[SolarReturnData]:
        """
        Calculate solar return for multiple locations.

        Useful for comparing how different locations affect
        the solar return chart (especially house placements).

        Args:
            natal_sun_longitude: Natal Sun longitude
            natal_date: Birth date
            year: Year for solar return
            locations: List of {"name", "latitude", "longitude"}
            house_system: House system

        Returns:
            List of SolarReturnData for each location
        """
        # First find the exact return time (same for all locations)
        jd_exact, precision = self.find_solar_return(
            natal_sun_longitude,
            year,
            natal_date.month,
            natal_date.day,
        )

        exact_dt = jd_to_datetime(jd_exact)
        positions = get_all_positions(jd_exact)

        returns = []

        for loc in locations:
            lat = loc.get("latitude", 0)
            lon = loc.get("longitude", 0)
            name = loc.get("name", "Unknown")

            # Calculate houses for this location
            houses = calculate_houses(jd_exact, lat, lon, house_system)

            # Aspects are the same, but recalculate with angles
            positions_with_angles = dict(positions)
            positions_with_angles["ascendant"] = {"longitude_decimal": houses.ascendant}
            positions_with_angles["mc"] = {"longitude_decimal": houses.mc}
            aspects = find_all_aspects(positions_with_angles, jd_exact)

            sr = SolarReturnData(
                year=year,
                exact_datetime_utc=exact_dt,
                jd_exact=jd_exact,
                sun_longitude=positions["sun"].longitude_decimal,
                natal_sun_longitude=natal_sun_longitude,
                precision_achieved=precision,
                positions=positions,
                houses=houses,
                aspects=aspects,
                latitude=lat,
                longitude=lon,
                location_name=name,
            )
            returns.append(sr)

        return returns


# Module-level convenience functions
_calculator = SolarReturnCalculator()


def calculate_solar_return(
    natal_sun_longitude: float,
    natal_date: datetime,
    year: int,
    latitude: float,
    longitude: float,
    location_name: str = "Location",
    house_system: str = "P",
) -> SolarReturnData:
    """Calculate a solar return chart."""
    return _calculator.calculate_solar_return(
        natal_sun_longitude,
        natal_date,
        year,
        latitude,
        longitude,
        location_name,
        house_system,
    )


def find_solar_return_time(
    natal_sun_longitude: float,
    year: int,
    natal_month: int,
    natal_day: int,
) -> datetime:
    """Find the exact datetime of a solar return."""
    jd, _ = _calculator.find_solar_return(
        natal_sun_longitude, year, natal_month, natal_day
    )
    return jd_to_datetime(jd)
