"""
Aspects Module - Detection and analysis of planetary aspects.

An aspect is an angular relationship between two celestial bodies.
This module calculates aspects with configurable orbs (tolerance ranges)
and determines whether aspects are applying (getting closer to exact)
or separating (moving away from exact).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd


# Default aspect definitions with orbs for major and minor planets
ASPECTS = {
    "conjunction": {"angle": 0, "orb_major": 8.0, "orb_minor": 6.0, "nature": "major"},
    "opposition": {"angle": 180, "orb_major": 8.0, "orb_minor": 6.0, "nature": "major"},
    "trine": {"angle": 120, "orb_major": 8.0, "orb_minor": 6.0, "nature": "major"},
    "square": {"angle": 90, "orb_major": 7.0, "orb_minor": 5.0, "nature": "major"},
    "sextile": {"angle": 60, "orb_major": 6.0, "orb_minor": 4.0, "nature": "major"},
    "quincunx": {"angle": 150, "orb_major": 3.0, "orb_minor": 2.0, "nature": "minor"},
    "semisextile": {"angle": 30, "orb_major": 2.0, "orb_minor": 1.0, "nature": "minor"},
    "semisquare": {"angle": 45, "orb_major": 2.0, "orb_minor": 1.0, "nature": "minor"},
    "sesquiquadrate": {"angle": 135, "orb_major": 2.0, "orb_minor": 1.0, "nature": "minor"},
    "quintile": {"angle": 72, "orb_major": 2.0, "orb_minor": 1.0, "nature": "minor"},
    "biquintile": {"angle": 144, "orb_major": 2.0, "orb_minor": 1.0, "nature": "minor"},
}

# Major planets (use wider orbs)
MAJOR_BODIES = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"}

# Aspect symbols
ASPECT_SYMBOLS = {
    "conjunction": "\u260C",
    "opposition": "\u260D",
    "trine": "\u25B3",
    "square": "\u25A1",
    "sextile": "\u2736",
    "quincunx": "Qx",
    "semisextile": "\u26BA",
    "semisquare": "\u2220",
    "sesquiquadrate": "\u26BC",
    "quintile": "Q",
    "biquintile": "bQ",
}


@dataclass
class AspectResult:
    """Result of aspect calculation between two bodies."""

    body1: str
    body2: str
    aspect_name: str
    aspect_angle: float  # Exact aspect angle (0, 60, 90, etc.)
    actual_angle: float  # Actual angle between bodies
    orb: float  # Difference from exact (always positive)
    orb_percent: float  # Percentage of maximum orb used
    is_applying: bool  # Getting closer to exact
    is_separating: bool  # Moving away from exact
    exact_date_estimate: Optional[datetime]  # Estimated date of exact aspect
    strength: float  # 1.0 = exact, 0.0 = at orb limit
    nature: str  # major or minor

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "body1": self.body1,
            "body2": self.body2,
            "aspect_name": self.aspect_name,
            "aspect_angle": self.aspect_angle,
            "actual_angle": self.actual_angle,
            "orb": self.orb,
            "orb_percent": self.orb_percent,
            "is_applying": self.is_applying,
            "is_separating": self.is_separating,
            "exact_date_estimate": (
                self.exact_date_estimate.isoformat() if self.exact_date_estimate else None
            ),
            "strength": self.strength,
            "nature": self.nature,
            "symbol": ASPECT_SYMBOLS.get(self.aspect_name, "?"),
        }

    def __str__(self) -> str:
        """String representation of aspect."""
        app_sep = "applying" if self.is_applying else "separating"
        symbol = ASPECT_SYMBOLS.get(self.aspect_name, "?")
        return (
            f"{self.body1} {symbol} {self.body2} "
            f"({self.aspect_name}, orb {self.orb:.2f}°, {app_sep})"
        )


class AspectEngine:
    """
    Engine for calculating and analyzing planetary aspects.

    Features:
    - Multiple aspect types with configurable orbs
    - Applying/separating detection using velocities
    - Strength calculation based on orb tightness
    - Aspect matrix generation
    """

    def __init__(
        self,
        aspects: Optional[dict] = None,
        include_minor: bool = True,
    ):
        """
        Initialize aspect engine.

        Args:
            aspects: Custom aspect definitions (optional)
            include_minor: Whether to include minor aspects
        """
        self.aspects = aspects or ASPECTS.copy()
        self.include_minor = include_minor

    def calculate_angle(self, lon1: float, lon2: float) -> float:
        """
        Calculate the angular separation between two longitudes.

        Args:
            lon1: First longitude (0-360)
            lon2: Second longitude (0-360)

        Returns:
            Angular separation (0-180)
        """
        diff = abs(lon1 - lon2)
        if diff > 180:
            diff = 360 - diff
        return diff

    def get_orb(self, aspect_name: str, body1: str, body2: str) -> float:
        """
        Get the orb for an aspect based on the bodies involved.

        Major bodies (Sun, Moon, planets to Saturn) get wider orbs.

        Args:
            aspect_name: Name of the aspect
            body1: First body name
            body2: Second body name

        Returns:
            Orb in degrees
        """
        aspect = self.aspects.get(aspect_name)
        if not aspect:
            return 1.0

        # Use major orb if either body is a major body
        if body1.lower() in MAJOR_BODIES or body2.lower() in MAJOR_BODIES:
            return aspect["orb_major"]
        return aspect["orb_minor"]

    def find_aspect(
        self,
        lon1: float,
        lon2: float,
        speed1: Optional[float] = None,
        speed2: Optional[float] = None,
        body1: str = "body1",
        body2: str = "body2",
        current_jd: Optional[float] = None,
    ) -> Optional[AspectResult]:
        """
        Find if two positions form an aspect.

        Args:
            lon1: Longitude of first body (0-360)
            lon2: Longitude of second body (0-360)
            speed1: Velocity of first body (degrees/day)
            speed2: Velocity of second body (degrees/day)
            body1: Name of first body
            body2: Name of second body
            current_jd: Current Julian Day (for exact date estimation)

        Returns:
            AspectResult if aspect found, None otherwise
        """
        actual_angle = self.calculate_angle(lon1, lon2)

        for aspect_name, aspect_def in self.aspects.items():
            # Skip minor aspects if not included
            if not self.include_minor and aspect_def["nature"] == "minor":
                continue

            target_angle = aspect_def["angle"]
            max_orb = self.get_orb(aspect_name, body1, body2)

            # Calculate orb (distance from exact aspect)
            if target_angle == 0:
                # Conjunction: actual angle is already the orb
                orb = actual_angle
            elif target_angle == 180:
                # Opposition: check distance from 180°
                orb = abs(actual_angle - 180)
            else:
                # Other aspects: check distance from target
                orb = abs(actual_angle - target_angle)

            # Check if within orb
            if orb <= max_orb:
                # Calculate strength (1.0 at exact, 0.0 at orb limit)
                strength = 1.0 - (orb / max_orb)
                orb_percent = (orb / max_orb) * 100

                # Determine applying/separating
                is_applying = False
                is_separating = False
                exact_date_estimate = None

                if speed1 is not None and speed2 is not None:
                    # Relative velocity
                    rel_speed = speed1 - speed2

                    # For conjunction: applying if faster body is behind
                    # For other aspects: more complex calculation
                    if target_angle == 0:
                        # Conjunction
                        diff = (lon1 - lon2 + 180) % 360 - 180
                        if (diff > 0 and rel_speed < 0) or (diff < 0 and rel_speed > 0):
                            is_applying = True
                        else:
                            is_separating = True
                    else:
                        # Other aspects: check if getting closer to target angle
                        # This is a simplified check
                        if abs(rel_speed) > 0.01:  # Meaningful relative motion
                            # Check direction of change
                            tomorrow_lon1 = (lon1 + speed1) % 360
                            tomorrow_lon2 = (lon2 + speed2) % 360
                            tomorrow_angle = self.calculate_angle(tomorrow_lon1, tomorrow_lon2)
                            tomorrow_orb = abs(tomorrow_angle - target_angle)

                            if tomorrow_orb < orb:
                                is_applying = True
                            else:
                                is_separating = True

                    # Estimate exact date
                    if is_applying and current_jd and abs(rel_speed) > 0.001:
                        # Rough estimate: days until orb = 0
                        days_to_exact = orb / abs(rel_speed)
                        # Convert to datetime (simplified)
                        if days_to_exact < 365:  # Only estimate within a year
                            from core.time_engine import jd_to_datetime

                            try:
                                exact_jd = current_jd + days_to_exact
                                exact_date_estimate = jd_to_datetime(exact_jd)
                            except Exception:
                                pass

                return AspectResult(
                    body1=body1,
                    body2=body2,
                    aspect_name=aspect_name,
                    aspect_angle=target_angle,
                    actual_angle=actual_angle,
                    orb=orb,
                    orb_percent=orb_percent,
                    is_applying=is_applying,
                    is_separating=is_separating,
                    exact_date_estimate=exact_date_estimate,
                    strength=strength,
                    nature=aspect_def["nature"],
                )

        return None

    def find_all_aspects(
        self,
        positions: dict,
        include_points: Optional[list] = None,
        current_jd: Optional[float] = None,
    ) -> list[AspectResult]:
        """
        Find all aspects between positions.

        Args:
            positions: Dictionary of body -> position data
            include_points: List of additional points (ASC, MC) to include
            current_jd: Current Julian Day for date estimation

        Returns:
            List of AspectResult objects
        """
        aspects = []
        bodies = list(positions.keys())

        if include_points:
            bodies.extend(include_points)

        # Check all unique pairs
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i + 1 :]:
                # Get positions
                pos1 = positions.get(body1)
                pos2 = positions.get(body2)

                if pos1 is None or pos2 is None:
                    continue

                # Extract longitude and speed
                if hasattr(pos1, "longitude_decimal"):
                    lon1 = pos1.longitude_decimal
                    speed1 = pos1.speed_longitude
                else:
                    lon1 = pos1.get("longitude_decimal", pos1.get("longitude", 0))
                    speed1 = pos1.get("speed_longitude", pos1.get("speed", None))

                if hasattr(pos2, "longitude_decimal"):
                    lon2 = pos2.longitude_decimal
                    speed2 = pos2.speed_longitude
                else:
                    lon2 = pos2.get("longitude_decimal", pos2.get("longitude", 0))
                    speed2 = pos2.get("speed_longitude", pos2.get("speed", None))

                # Find aspect
                aspect = self.find_aspect(
                    lon1, lon2, speed1, speed2, body1, body2, current_jd
                )
                if aspect:
                    aspects.append(aspect)

        return aspects

    def aspect_matrix(
        self,
        positions: dict,
        include_minor: bool = True,
    ) -> pd.DataFrame:
        """
        Generate a matrix of aspects between all bodies.

        Args:
            positions: Dictionary of body -> position data
            include_minor: Whether to include minor aspects

        Returns:
            DataFrame with aspects (triangular matrix)
        """
        bodies = list(positions.keys())
        n = len(bodies)

        # Create empty matrix
        matrix = pd.DataFrame(
            index=bodies,
            columns=bodies,
            data="",
        )

        # Fill upper triangle with aspects
        for i, body1 in enumerate(bodies):
            for j, body2 in enumerate(bodies):
                if i >= j:
                    continue

                pos1 = positions[body1]
                pos2 = positions[body2]

                if hasattr(pos1, "longitude_decimal"):
                    lon1 = pos1.longitude_decimal
                    speed1 = pos1.speed_longitude
                else:
                    lon1 = pos1.get("longitude_decimal", 0)
                    speed1 = pos1.get("speed_longitude")

                if hasattr(pos2, "longitude_decimal"):
                    lon2 = pos2.longitude_decimal
                    speed2 = pos2.speed_longitude
                else:
                    lon2 = pos2.get("longitude_decimal", 0)
                    speed2 = pos2.get("speed_longitude")

                # Temporarily set include_minor
                old_include = self.include_minor
                self.include_minor = include_minor

                aspect = self.find_aspect(lon1, lon2, speed1, speed2, body1, body2)

                self.include_minor = old_include

                if aspect:
                    symbol = ASPECT_SYMBOLS.get(aspect.aspect_name, "?")
                    app = "a" if aspect.is_applying else "s"
                    matrix.loc[body1, body2] = f"{symbol}{aspect.orb:.1f}°{app}"

        return matrix


def calculate_aspect_summary(aspects: list[AspectResult]) -> dict:
    """
    Calculate summary statistics for a list of aspects.

    Args:
        aspects: List of AspectResult objects

    Returns:
        Dictionary with summary statistics
    """
    if not aspects:
        return {
            "total": 0,
            "major": 0,
            "minor": 0,
            "applying": 0,
            "separating": 0,
            "by_type": {},
            "average_orb": 0,
            "tightest": None,
        }

    major = [a for a in aspects if a.nature == "major"]
    minor = [a for a in aspects if a.nature == "minor"]
    applying = [a for a in aspects if a.is_applying]
    separating = [a for a in aspects if a.is_separating]

    # Count by type
    by_type = {}
    for aspect in aspects:
        name = aspect.aspect_name
        by_type[name] = by_type.get(name, 0) + 1

    # Average orb
    avg_orb = sum(a.orb for a in aspects) / len(aspects)

    # Tightest aspect
    tightest = min(aspects, key=lambda a: a.orb)

    return {
        "total": len(aspects),
        "major": len(major),
        "minor": len(minor),
        "applying": len(applying),
        "separating": len(separating),
        "by_type": by_type,
        "average_orb": avg_orb,
        "tightest": tightest.to_dict() if tightest else None,
    }


# Module-level convenience instance
_engine = AspectEngine()


def find_aspect(
    lon1: float,
    lon2: float,
    speed1: Optional[float] = None,
    speed2: Optional[float] = None,
    body1: str = "body1",
    body2: str = "body2",
) -> Optional[AspectResult]:
    """Find aspect between two positions."""
    return _engine.find_aspect(lon1, lon2, speed1, speed2, body1, body2)


def find_all_aspects(positions: dict, current_jd: Optional[float] = None) -> list:
    """Find all aspects between positions."""
    return _engine.find_all_aspects(positions, current_jd=current_jd)


def aspect_matrix(positions: dict, include_minor: bool = True) -> pd.DataFrame:
    """Generate aspect matrix."""
    return _engine.aspect_matrix(positions, include_minor)
