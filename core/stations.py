"""
Stations Module - Planetary station detection.

A station occurs when a planet's longitudinal velocity becomes zero,
appearing to stop before reversing direction. This module finds
these critical moments with high precision.

Types of stations:
- Retrograde station: Planet stops before moving backward
- Direct station: Planet stops before resuming forward motion
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from core.ephemeris import get_position, BODY_MAP
from core.time_engine import datetime_to_jd, jd_to_datetime
from data.symbols import longitude_to_zodiacal


@dataclass
class StationEvent:
    """A planetary station event."""

    jd: float
    datetime_utc: datetime
    body: str
    station_type: str  # 'retrograde' or 'direct'
    longitude: float
    longitude_zodiacal: str
    speed_before: float  # Speed 1 day before
    speed_after: float  # Speed 1 day after

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "jd": self.jd,
            "datetime_utc": self.datetime_utc.isoformat(),
            "body": self.body,
            "station_type": self.station_type,
            "longitude": self.longitude,
            "longitude_zodiacal": self.longitude_zodiacal,
            "speed_before": self.speed_before,
            "speed_after": self.speed_after,
        }

    def __str__(self) -> str:
        """String representation."""
        symbol = "℞" if self.station_type == "retrograde" else "D"
        return (
            f"{self.body.capitalize()} station {self.station_type} {symbol} "
            f"at {self.longitude_zodiacal} - "
            f"{self.datetime_utc.strftime('%Y-%m-%d %H:%M')}"
        )


class StationFinder:
    """
    Find planetary stations with high precision.

    Uses bisection to find the exact moment when velocity = 0.
    """

    # Default precision: ~8.6 seconds
    DEFAULT_PRECISION = 0.0001  # days

    # Scan step (days)
    SCAN_STEP = 1.0

    # Bodies that can be retrograde (exclude Sun and Moon)
    STATION_BODIES = [
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
    ]

    def __init__(self, precision_days: float = None):
        """
        Initialize station finder.

        Args:
            precision_days: Precision for finding station time
        """
        self.precision = precision_days or self.DEFAULT_PRECISION

    def find_stations(
        self,
        body: str,
        start_jd: float,
        end_jd: float,
    ) -> list[StationEvent]:
        """
        Find all stations of a body within a date range.

        Args:
            body: Body name (e.g., 'mars', 'jupiter')
            start_jd: Start Julian Day
            end_jd: End Julian Day

        Returns:
            List of StationEvent objects
        """
        if body.lower() in ["sun", "moon"]:
            return []  # Sun and Moon don't have stations

        stations = []
        current_jd = start_jd

        prev_speed = None

        while current_jd < end_jd:
            pos = get_position(body, current_jd)
            speed = pos.speed_longitude

            if prev_speed is not None:
                # Check for sign change in velocity
                if prev_speed * speed < 0:
                    # Station occurred between prev and current
                    station_jd = self._bisect_to_station(
                        body, current_jd - self.SCAN_STEP, current_jd
                    )

                    if station_jd:
                        # Determine station type
                        station_pos = get_position(body, station_jd)

                        # Get speeds before and after
                        speed_before = get_position(body, station_jd - 1).speed_longitude
                        speed_after = get_position(body, station_jd + 1).speed_longitude

                        # Retrograde if speed goes from positive to negative
                        if speed_before > 0 and speed_after < 0:
                            station_type = "retrograde"
                        else:
                            station_type = "direct"

                        event = StationEvent(
                            jd=station_jd,
                            datetime_utc=jd_to_datetime(station_jd),
                            body=body,
                            station_type=station_type,
                            longitude=station_pos.longitude_decimal,
                            longitude_zodiacal=station_pos.longitude_zodiacal,
                            speed_before=speed_before,
                            speed_after=speed_after,
                        )
                        stations.append(event)

            prev_speed = speed
            current_jd += self.SCAN_STEP

        return stations

    def _bisect_to_station(
        self,
        body: str,
        jd_start: float,
        jd_end: float,
    ) -> Optional[float]:
        """
        Use bisection to find exact station time (velocity = 0).

        Args:
            body: Body name
            jd_start: Start of search interval
            jd_end: End of search interval

        Returns:
            Julian Day of station, or None if not found
        """
        speed_start = get_position(body, jd_start).speed_longitude
        speed_end = get_position(body, jd_end).speed_longitude

        # Verify sign change
        if speed_start * speed_end > 0:
            return None

        iterations = 0
        max_iterations = 50

        while (jd_end - jd_start) > self.precision and iterations < max_iterations:
            jd_mid = (jd_start + jd_end) / 2
            speed_mid = get_position(body, jd_mid).speed_longitude

            if speed_mid * speed_start < 0:
                jd_end = jd_mid
                speed_end = speed_mid
            else:
                jd_start = jd_mid
                speed_start = speed_mid

            iterations += 1

        return (jd_start + jd_end) / 2

    def find_all_stations(
        self,
        start_date: datetime,
        end_date: datetime,
        bodies: Optional[list] = None,
    ) -> list[StationEvent]:
        """
        Find all stations for multiple bodies.

        Args:
            start_date: Start datetime
            end_date: End datetime
            bodies: List of bodies (default: all station bodies)

        Returns:
            List of StationEvent objects, sorted by date
        """
        if bodies is None:
            bodies = self.STATION_BODIES

        start_jd = datetime_to_jd(start_date)
        end_jd = datetime_to_jd(end_date)

        all_stations = []

        for body in bodies:
            stations = self.find_stations(body, start_jd, end_jd)
            all_stations.extend(stations)

        # Sort by date
        all_stations.sort(key=lambda s: s.jd)

        return all_stations

    def get_retrograde_periods(
        self,
        body: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """
        Get retrograde periods for a body.

        Returns list of {start, end, start_longitude, end_longitude}
        """
        start_jd = datetime_to_jd(start_date)
        end_jd = datetime_to_jd(end_date)

        stations = self.find_stations(body, start_jd, end_jd)

        periods = []
        retro_start = None

        for station in stations:
            if station.station_type == "retrograde":
                retro_start = station
            elif station.station_type == "direct" and retro_start:
                periods.append(
                    {
                        "start": retro_start.datetime_utc,
                        "end": station.datetime_utc,
                        "start_longitude": retro_start.longitude,
                        "start_zodiacal": retro_start.longitude_zodiacal,
                        "end_longitude": station.longitude,
                        "end_zodiacal": station.longitude_zodiacal,
                        "duration_days": station.jd - retro_start.jd,
                    }
                )
                retro_start = None

        return periods


# Module-level convenience instance
_finder = StationFinder()


def find_stations(
    body: str,
    start_date: datetime,
    end_date: datetime,
) -> list[StationEvent]:
    """Find stations for a body."""
    start_jd = datetime_to_jd(start_date)
    end_jd = datetime_to_jd(end_date)
    return _finder.find_stations(body, start_jd, end_jd)


def find_all_stations(
    start_date: datetime,
    end_date: datetime,
    bodies: Optional[list] = None,
) -> list[StationEvent]:
    """Find all stations for multiple bodies."""
    return _finder.find_all_stations(start_date, end_date, bodies)


def get_retrograde_periods(
    body: str,
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    """Get retrograde periods for a body."""
    return _finder.get_retrograde_periods(body, start_date, end_date)
