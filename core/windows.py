"""
Activation Windows Module - Transit activity analysis.

This module calculates when natal points are "activated" by transits,
quantifying the intensity of transit activity over time.

Features:
- Daily activation levels for natal points
- Peak window identification
- Aggregate intensity calculation
- Transit theme analysis
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from core.ephemeris import get_position
from core.time_engine import datetime_to_jd, jd_to_datetime
from core.aspects import ASPECTS


@dataclass
class ActivationWindow:
    """A window of high transit activation."""

    start: datetime
    end: datetime
    peak: datetime
    intensity: float  # 0-1 normalized
    primary_transits: list[str]
    activated_points: list[str]
    theme: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "peak": self.peak.isoformat(),
            "duration_days": (self.end - self.start).days,
            "intensity": self.intensity,
            "primary_transits": self.primary_transits,
            "activated_points": self.activated_points,
            "theme": self.theme,
        }


class ActivationEngine:
    """
    Calculate transit activation levels for natal points.

    Activation is based on orb distance from exact aspects,
    with tighter orbs giving higher activation values.
    """

    # Default transiting bodies to track
    DEFAULT_TRANSITING_BODIES = [
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
    ]

    # Default aspects to consider
    DEFAULT_ASPECTS = ["conjunction", "opposition", "trine", "square", "sextile"]

    # Weights for different transiting bodies (outer = stronger effect)
    BODY_WEIGHTS = {
        "jupiter": 0.6,
        "saturn": 0.8,
        "uranus": 1.0,
        "neptune": 1.0,
        "pluto": 1.0,
    }

    # Default orbs for transit activation
    TRANSIT_ORBS = {
        "conjunction": 3.0,
        "opposition": 3.0,
        "trine": 2.5,
        "square": 2.5,
        "sextile": 2.0,
    }

    def __init__(self, orbs: Optional[dict] = None):
        """
        Initialize activation engine.

        Args:
            orbs: Custom orbs for transit activation
        """
        self.orbs = orbs or self.TRANSIT_ORBS

    def calculate_single_activation(
        self,
        transiting_lon: float,
        natal_lon: float,
        aspect_angle: float,
        max_orb: float,
    ) -> float:
        """
        Calculate activation level for a single transit/aspect combination.

        Returns value from 0 (outside orb) to 1 (exact aspect).
        """
        # Calculate actual angle
        diff = abs(transiting_lon - natal_lon)
        if diff > 180:
            diff = 360 - diff

        # Distance from exact aspect
        if aspect_angle == 0:
            orb = diff
        elif aspect_angle == 180:
            orb = abs(diff - 180)
        else:
            orb = abs(diff - aspect_angle)

        # If outside orb, no activation
        if orb > max_orb:
            return 0.0

        # Linear falloff from 1.0 (exact) to 0.0 (at orb edge)
        activation = 1.0 - (orb / max_orb)

        return activation

    def calculate_activation(
        self,
        natal_point: str,
        natal_position: float,
        start_date: datetime,
        end_date: datetime,
        resolution_days: float = 1.0,
        transiting_bodies: Optional[list] = None,
        aspects: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Calculate daily activation levels for a natal point.

        Args:
            natal_point: Name of natal point
            natal_position: Longitude of natal point (0-360)
            start_date: Start of analysis period
            end_date: End of analysis period
            resolution_days: Time step in days
            transiting_bodies: Bodies to track
            aspects: Aspects to consider

        Returns:
            DataFrame with columns: date, [body]_activation, total_activation, active_aspects
        """
        if transiting_bodies is None:
            transiting_bodies = self.DEFAULT_TRANSITING_BODIES

        if aspects is None:
            aspects = self.DEFAULT_ASPECTS

        # Generate date range
        current_date = start_date
        records = []

        while current_date <= end_date:
            jd = datetime_to_jd(current_date)
            record = {"date": current_date}

            total_weighted = 0.0
            total_weight = 0.0
            active_aspects = []

            for body in transiting_bodies:
                pos = get_position(body, jd)
                body_lon = pos.longitude_decimal

                max_activation = 0.0
                max_aspect = None

                for aspect_name in aspects:
                    aspect_angle = ASPECTS[aspect_name]["angle"]
                    orb = self.orbs.get(aspect_name, 2.0)

                    activation = self.calculate_single_activation(
                        body_lon, natal_position, aspect_angle, orb
                    )

                    if activation > max_activation:
                        max_activation = activation
                        max_aspect = aspect_name

                record[f"{body}_activation"] = max_activation

                if max_activation > 0:
                    active_aspects.append(f"{body}_{max_aspect}")

                    weight = self.BODY_WEIGHTS.get(body, 1.0)
                    total_weighted += max_activation * weight
                    total_weight += weight

            # Calculate total activation (weighted average)
            if total_weight > 0:
                record["total_activation"] = total_weighted / total_weight
            else:
                record["total_activation"] = 0.0

            record["active_aspects"] = active_aspects

            records.append(record)
            current_date += timedelta(days=resolution_days)

        return pd.DataFrame(records)

    def calculate_multi_point_activation(
        self,
        natal_positions: dict,
        start_date: datetime,
        end_date: datetime,
        resolution_days: float = 1.0,
        focus_points: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Calculate activation for multiple natal points.

        Args:
            natal_positions: Dictionary of point name -> longitude
            start_date: Start date
            end_date: End date
            resolution_days: Resolution
            focus_points: Which points to analyze (default: all)

        Returns:
            DataFrame with activation levels for all points
        """
        if focus_points is None:
            focus_points = list(natal_positions.keys())

        # Start with date column
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=resolution_days)

        result = pd.DataFrame({"date": dates})

        for point in focus_points:
            if point not in natal_positions:
                continue

            lon = natal_positions[point]

            # Handle different position formats
            if hasattr(lon, "longitude_decimal"):
                lon = lon.longitude_decimal
            elif isinstance(lon, dict):
                lon = lon.get("longitude_decimal", lon.get("longitude", 0))

            # Calculate activation for this point
            point_df = self.calculate_activation(
                point, lon, start_date, end_date, resolution_days
            )

            result[f"{point}_activation"] = point_df["total_activation"]

        # Overall activation (max of all points)
        activation_cols = [c for c in result.columns if c.endswith("_activation")]
        if activation_cols:
            result["max_activation"] = result[activation_cols].max(axis=1)
            result["mean_activation"] = result[activation_cols].mean(axis=1)

        return result

    def find_peak_windows(
        self,
        natal_positions: dict,
        start_date: datetime,
        end_date: datetime,
        focus_points: Optional[list] = None,
        threshold: float = 0.5,
        min_duration_days: int = 3,
    ) -> list[ActivationWindow]:
        """
        Identify windows of high transit activity.

        Args:
            natal_positions: Natal point longitudes
            start_date: Start date
            end_date: End date
            focus_points: Points to analyze
            threshold: Minimum activation level for a window
            min_duration_days: Minimum window duration

        Returns:
            List of ActivationWindow objects
        """
        if focus_points is None:
            focus_points = ["sun", "moon", "mercury", "ascendant", "mc"]
            focus_points = [p for p in focus_points if p in natal_positions]

        # Calculate daily activation
        df = self.calculate_multi_point_activation(
            natal_positions, start_date, end_date, 1.0, focus_points
        )

        windows = []
        in_window = False
        window_start = None
        window_data = []

        for _, row in df.iterrows():
            above_threshold = row.get("max_activation", 0) >= threshold

            if above_threshold:
                if not in_window:
                    # Start new window
                    in_window = True
                    window_start = row["date"]
                    window_data = []
                window_data.append(row)
            else:
                if in_window:
                    # Close window
                    window_end = row["date"]
                    duration = (window_end - window_start).days

                    if duration >= min_duration_days:
                        # Find peak
                        peak_row = max(window_data, key=lambda r: r.get("max_activation", 0))

                        # Determine which points are most activated
                        activation_cols = [c for c in df.columns if c.endswith("_activation") and c != "max_activation" and c != "mean_activation"]
                        activated = []
                        for col in activation_cols:
                            point = col.replace("_activation", "")
                            if peak_row.get(col, 0) > 0.3:
                                activated.append(point)

                        # Determine theme based on activated points
                        theme = self._determine_theme(activated)

                        window = ActivationWindow(
                            start=window_start,
                            end=window_end,
                            peak=peak_row["date"],
                            intensity=peak_row.get("max_activation", 0),
                            primary_transits=[],  # Would need more detailed analysis
                            activated_points=activated,
                            theme=theme,
                        )
                        windows.append(window)

                    in_window = False
                    window_data = []

        # Handle window that extends to end date
        if in_window and len(window_data) >= min_duration_days:
            peak_row = max(window_data, key=lambda r: r.get("max_activation", 0))
            activation_cols = [c for c in df.columns if c.endswith("_activation") and c != "max_activation" and c != "mean_activation"]
            activated = [
                c.replace("_activation", "")
                for c in activation_cols
                if peak_row.get(c, 0) > 0.3
            ]
            theme = self._determine_theme(activated)

            window = ActivationWindow(
                start=window_start,
                end=end_date,
                peak=peak_row["date"],
                intensity=peak_row.get("max_activation", 0),
                primary_transits=[],
                activated_points=activated,
                theme=theme,
            )
            windows.append(window)

        return windows

    def _determine_theme(self, activated_points: list[str]) -> str:
        """Determine theme based on activated natal points."""
        themes = []

        if "sun" in activated_points:
            themes.append("identity/vitality")
        if "moon" in activated_points:
            themes.append("emotions/home")
        if "mercury" in activated_points:
            themes.append("communication/thought")
        if "venus" in activated_points:
            themes.append("relationships/values")
        if "mars" in activated_points:
            themes.append("action/energy")
        if "jupiter" in activated_points:
            themes.append("expansion/growth")
        if "saturn" in activated_points:
            themes.append("structure/responsibility")
        if "ascendant" in activated_points:
            themes.append("self-expression/appearance")
        if "mc" in activated_points:
            themes.append("career/public life")

        if not themes:
            return "general activity"

        return " + ".join(themes[:3])  # Limit to top 3


# Module-level convenience functions
_engine = ActivationEngine()


def calculate_activation(
    natal_point: str,
    natal_position: float,
    start_date: datetime,
    end_date: datetime,
    resolution_days: float = 1.0,
) -> pd.DataFrame:
    """Calculate daily activation for a natal point."""
    return _engine.calculate_activation(
        natal_point, natal_position, start_date, end_date, resolution_days
    )


def find_peak_windows(
    natal_positions: dict,
    start_date: datetime,
    end_date: datetime,
    focus_points: Optional[list] = None,
) -> list[ActivationWindow]:
    """Find windows of high transit activity."""
    return _engine.find_peak_windows(
        natal_positions, start_date, end_date, focus_points
    )
