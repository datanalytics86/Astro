"""
Transits Module - High-precision transit detection.

This module finds exact times when transiting planets form aspects
to natal positions. It uses bisection and refinement algorithms
to achieve precision of approximately 8.6 seconds (0.0001 days).

Features:
- Find exact aspect times with high precision
- Handle retrograde motion (multiple passes)
- Calculate transit timelines
- Generate transit reports
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import swisseph as swe

from core.ephemeris import BODY_MAP, get_position
from core.time_engine import datetime_to_jd, jd_to_datetime
from core.aspects import ASPECTS


@dataclass
class TransitEvent:
    """A single transit event (exact aspect)."""

    jd_exact: float
    datetime_utc: datetime
    transiting_body: str
    transiting_position: float
    natal_point: str
    natal_position: float
    aspect: str
    aspect_angle: float
    pass_number: int  # 1, 2, 3 for multiple passes
    is_retrograde: bool
    speed_at_exact: float
    orb_at_search_start: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "jd_exact": self.jd_exact,
            "datetime_utc": self.datetime_utc.isoformat(),
            "transiting_body": self.transiting_body,
            "transiting_position": self.transiting_position,
            "natal_point": self.natal_point,
            "natal_position": self.natal_position,
            "aspect": self.aspect,
            "aspect_angle": self.aspect_angle,
            "pass_number": self.pass_number,
            "is_retrograde": self.is_retrograde,
            "speed_at_exact": self.speed_at_exact,
        }

    def __str__(self) -> str:
        """String representation."""
        retro = " (R)" if self.is_retrograde else ""
        return (
            f"{self.transiting_body.capitalize()}{retro} {self.aspect} "
            f"natal {self.natal_point.capitalize()} - "
            f"{self.datetime_utc.strftime('%Y-%m-%d %H:%M')}"
        )


class TransitFinder:
    """
    High-precision transit finder.

    Uses bisection algorithm with Newton-Raphson refinement
    to find exact aspect times.
    """

    # Default precision: ~8.6 seconds
    DEFAULT_PRECISION = 0.0001  # days

    # Step size for initial scan (days)
    SCAN_STEP = 1.0

    def __init__(self, precision_days: float = None):
        """
        Initialize transit finder.

        Args:
            precision_days: Precision for exact time finding (default ~8.6 sec)
        """
        self.precision = precision_days or self.DEFAULT_PRECISION

    def _get_position_at_jd(self, body: str, jd: float) -> tuple[float, float]:
        """
        Get longitude and speed at a Julian Day.

        Returns:
            (longitude, speed_per_day)
        """
        pos = get_position(body, jd)
        return pos.longitude_decimal, pos.speed_longitude

    def _calculate_aspect_distance(
        self,
        transiting_lon: float,
        natal_lon: float,
        aspect_angle: float,
    ) -> float:
        """
        Calculate signed distance from exact aspect.

        Positive = transiting body needs to move forward
        Negative = transiting body has passed the aspect
        """
        # Target longitude for aspect
        target = (natal_lon + aspect_angle) % 360

        # Distance from target
        diff = transiting_lon - target

        # Normalize to -180 to +180
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        return diff

    def find_exact_aspect(
        self,
        transiting_body: str,
        natal_position: float,
        aspect_angle: float,
        start_jd: float,
        end_jd: float,
        natal_point_name: str = "point",
    ) -> list[TransitEvent]:
        """
        Find all exact aspect times within a date range.

        Handles retrograde motion which can cause 1, 3, or 5 passes
        over the same point.

        Args:
            transiting_body: Name of transiting planet
            natal_position: Natal longitude (0-360)
            aspect_angle: Aspect angle (0, 60, 90, 120, 180, etc.)
            start_jd: Start Julian Day
            end_jd: End Julian Day
            natal_point_name: Name of natal point for labeling

        Returns:
            List of TransitEvent objects
        """
        events = []
        current_jd = start_jd

        # Track sign changes in aspect distance
        prev_dist = None
        pass_number = 1

        while current_jd < end_jd:
            lon, speed = self._get_position_at_jd(transiting_body, current_jd)
            dist = self._calculate_aspect_distance(lon, natal_position, aspect_angle)

            # Check for sign change (crossing the exact aspect)
            if prev_dist is not None:
                crossed = False

                # Direct motion crossing
                if prev_dist < 0 and dist >= 0:
                    crossed = True
                elif prev_dist > 0 and dist <= 0:
                    crossed = True

                # Also check for retrograde back-crossing
                if abs(dist - prev_dist) > 180:
                    # Wrapped around, reset
                    pass

                if crossed and abs(dist) < 30:  # Sanity check
                    # Refine to find exact moment
                    exact_jd = self._bisect_to_exact(
                        transiting_body,
                        natal_position,
                        aspect_angle,
                        current_jd - self.SCAN_STEP,
                        current_jd,
                    )

                    if exact_jd:
                        exact_lon, exact_speed = self._get_position_at_jd(
                            transiting_body, exact_jd
                        )

                        event = TransitEvent(
                            jd_exact=exact_jd,
                            datetime_utc=jd_to_datetime(exact_jd),
                            transiting_body=transiting_body,
                            transiting_position=exact_lon,
                            natal_point=natal_point_name,
                            natal_position=natal_position,
                            aspect=self._get_aspect_name(aspect_angle),
                            aspect_angle=aspect_angle,
                            pass_number=pass_number,
                            is_retrograde=exact_speed < 0,
                            speed_at_exact=exact_speed,
                            orb_at_search_start=abs(prev_dist),
                        )
                        events.append(event)
                        pass_number += 1

            prev_dist = dist
            current_jd += self.SCAN_STEP

        # Renumber passes based on chronological order
        events.sort(key=lambda e: e.jd_exact)
        for i, event in enumerate(events):
            event.pass_number = i + 1

        return events

    def _bisect_to_exact(
        self,
        body: str,
        natal_lon: float,
        aspect_angle: float,
        jd_start: float,
        jd_end: float,
    ) -> Optional[float]:
        """
        Use bisection to find exact aspect time.

        Args:
            body: Transiting body name
            natal_lon: Natal longitude
            aspect_angle: Aspect angle
            jd_start: Start of search interval
            jd_end: End of search interval

        Returns:
            Julian Day of exact aspect, or None if not found
        """
        # Initial distances
        lon_start, _ = self._get_position_at_jd(body, jd_start)
        lon_end, _ = self._get_position_at_jd(body, jd_end)

        dist_start = self._calculate_aspect_distance(lon_start, natal_lon, aspect_angle)
        dist_end = self._calculate_aspect_distance(lon_end, natal_lon, aspect_angle)

        # Verify sign change
        if dist_start * dist_end > 0:
            return None

        # Bisection
        iterations = 0
        max_iterations = 50

        while (jd_end - jd_start) > self.precision and iterations < max_iterations:
            jd_mid = (jd_start + jd_end) / 2
            lon_mid, _ = self._get_position_at_jd(body, jd_mid)
            dist_mid = self._calculate_aspect_distance(lon_mid, natal_lon, aspect_angle)

            if dist_mid * dist_start < 0:
                jd_end = jd_mid
                dist_end = dist_mid
            else:
                jd_start = jd_mid
                dist_start = dist_mid

            iterations += 1

        return (jd_start + jd_end) / 2

    def _get_aspect_name(self, angle: float) -> str:
        """Get aspect name from angle."""
        for name, data in ASPECTS.items():
            if abs(data["angle"] - angle) < 1:
                return name
        return f"aspect_{int(angle)}"

    def find_all_transits(
        self,
        natal_positions: dict,
        start_date: datetime,
        end_date: datetime,
        transiting_bodies: Optional[list] = None,
        aspects: Optional[list] = None,
        natal_points: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Find all transits in a date range.

        Args:
            natal_positions: Dictionary of natal point -> longitude
            start_date: Start datetime
            end_date: End datetime
            transiting_bodies: Bodies to track (default: outer planets)
            aspects: Aspect types to find (default: major aspects)
            natal_points: Natal points to check (default: all)

        Returns:
            DataFrame with all transit events
        """
        if transiting_bodies is None:
            transiting_bodies = ["jupiter", "saturn", "uranus", "neptune", "pluto"]

        if aspects is None:
            aspects = ["conjunction", "opposition", "trine", "square", "sextile"]

        if natal_points is None:
            natal_points = list(natal_positions.keys())

        # Convert dates to JD
        start_jd = datetime_to_jd(start_date)
        end_jd = datetime_to_jd(end_date)

        all_events = []

        for body in transiting_bodies:
            for point in natal_points:
                if point not in natal_positions:
                    continue

                natal_lon = natal_positions[point]

                # Handle different position formats
                if hasattr(natal_lon, "longitude_decimal"):
                    natal_lon = natal_lon.longitude_decimal
                elif isinstance(natal_lon, dict):
                    natal_lon = natal_lon.get("longitude_decimal", natal_lon.get("longitude", 0))

                for aspect_name in aspects:
                    aspect_angle = ASPECTS[aspect_name]["angle"]

                    events = self.find_exact_aspect(
                        body,
                        natal_lon,
                        aspect_angle,
                        start_jd,
                        end_jd,
                        natal_point_name=point,
                    )
                    all_events.extend(events)

        # Convert to DataFrame
        if not all_events:
            return pd.DataFrame(
                columns=[
                    "datetime",
                    "transiting_body",
                    "aspect",
                    "natal_point",
                    "is_retrograde",
                    "pass_number",
                ]
            )

        data = [e.to_dict() for e in all_events]
        df = pd.DataFrame(data)
        df = df.sort_values("datetime_utc")
        df = df.reset_index(drop=True)

        return df


class TransitTimeline:
    """
    Generate transit timelines with orb periods.

    Shows when transits are within orb, not just exact times.
    """

    def __init__(self, orb: float = 2.0):
        """
        Initialize timeline generator.

        Args:
            orb: Orb to use for transit activity (degrees)
        """
        self.orb = orb

    def calculate_transit_activity(
        self,
        transiting_body: str,
        natal_position: float,
        aspect_angle: float,
        start_jd: float,
        end_jd: float,
        step_days: float = 1.0,
    ) -> list[dict]:
        """
        Calculate daily transit activity (orb-based).

        Returns list of {jd, date, orb, is_within_orb, is_applying}
        """
        activity = []
        current_jd = start_jd

        prev_orb = None

        while current_jd <= end_jd:
            pos = get_position(transiting_body, current_jd)
            lon = pos.longitude_decimal
            speed = pos.speed_longitude

            # Calculate orb from exact aspect
            target = (natal_position + aspect_angle) % 360
            diff = abs(lon - target)
            if diff > 180:
                diff = 360 - diff
            current_orb = diff

            # Determine if applying
            is_applying = False
            if prev_orb is not None:
                is_applying = current_orb < prev_orb

            activity.append(
                {
                    "jd": current_jd,
                    "date": jd_to_datetime(current_jd),
                    "longitude": lon,
                    "orb": current_orb,
                    "is_within_orb": current_orb <= self.orb,
                    "is_applying": is_applying,
                    "is_retrograde": speed < 0,
                }
            )

            prev_orb = current_orb
            current_jd += step_days

        return activity

    def find_transit_windows(
        self,
        transiting_body: str,
        natal_position: float,
        aspect_angle: float,
        start_jd: float,
        end_jd: float,
    ) -> list[dict]:
        """
        Find windows when transit is within orb.

        Returns list of {start, end, peak, peak_orb, aspect}
        """
        activity = self.calculate_transit_activity(
            transiting_body, natal_position, aspect_angle, start_jd, end_jd
        )

        windows = []
        current_window = None

        for point in activity:
            if point["is_within_orb"]:
                if current_window is None:
                    # Start new window
                    current_window = {
                        "start": point["date"],
                        "start_jd": point["jd"],
                        "min_orb": point["orb"],
                        "peak_date": point["date"],
                        "aspect": self._get_aspect_name(aspect_angle),
                    }
                else:
                    # Update if this is closer to exact
                    if point["orb"] < current_window["min_orb"]:
                        current_window["min_orb"] = point["orb"]
                        current_window["peak_date"] = point["date"]
            else:
                if current_window is not None:
                    # Close window
                    current_window["end"] = point["date"]
                    current_window["end_jd"] = point["jd"]
                    windows.append(current_window)
                    current_window = None

        # Close any open window
        if current_window is not None:
            current_window["end"] = activity[-1]["date"]
            current_window["end_jd"] = activity[-1]["jd"]
            windows.append(current_window)

        return windows

    def _get_aspect_name(self, angle: float) -> str:
        """Get aspect name from angle."""
        for name, data in ASPECTS.items():
            if abs(data["angle"] - angle) < 1:
                return name
        return f"aspect_{int(angle)}"


# Module-level convenience functions
_finder = TransitFinder()
_timeline = TransitTimeline()


def find_transit(
    transiting_body: str,
    natal_position: float,
    aspect_angle: float,
    start_date: datetime,
    end_date: datetime,
) -> list[TransitEvent]:
    """Find exact transit times."""
    start_jd = datetime_to_jd(start_date)
    end_jd = datetime_to_jd(end_date)
    return _finder.find_exact_aspect(
        transiting_body, natal_position, aspect_angle, start_jd, end_jd
    )


def find_all_transits(
    natal_positions: dict,
    start_date: datetime,
    end_date: datetime,
    transiting_bodies: Optional[list] = None,
    aspects: Optional[list] = None,
) -> pd.DataFrame:
    """Find all transits in date range."""
    return _finder.find_all_transits(
        natal_positions, start_date, end_date, transiting_bodies, aspects
    )
