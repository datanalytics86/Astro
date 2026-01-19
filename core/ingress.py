"""
Ingress Module - Sign change detection.

An ingress occurs when a celestial body crosses from one zodiac sign
to another. This module finds these moments with high precision.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from core.ephemeris import get_position
from core.time_engine import datetime_to_jd, jd_to_datetime
from data.symbols import ZODIAC_SIGNS, get_zodiac_sign


@dataclass
class IngressEvent:
    """A sign ingress event."""

    jd: float
    datetime_utc: datetime
    body: str
    from_sign: str
    to_sign: str
    longitude_exact: float  # Should be 0, 30, 60, etc.
    is_retrograde: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "jd": self.jd,
            "datetime_utc": self.datetime_utc.isoformat(),
            "body": self.body,
            "from_sign": self.from_sign,
            "to_sign": self.to_sign,
            "longitude_exact": self.longitude_exact,
            "is_retrograde": self.is_retrograde,
        }

    def __str__(self) -> str:
        """String representation."""
        direction = "(R)" if self.is_retrograde else ""
        return (
            f"{self.body.capitalize()} {direction} enters {self.to_sign} "
            f"(from {self.from_sign}) - "
            f"{self.datetime_utc.strftime('%Y-%m-%d %H:%M')}"
        )


class IngressFinder:
    """
    Find sign ingresses with high precision.

    Detects when planets cross sign boundaries (0°, 30°, 60°, etc.)
    """

    # Default precision: ~8.6 seconds
    DEFAULT_PRECISION = 0.0001  # days

    # Scan step (days)
    SCAN_STEP = 1.0

    def __init__(self, precision_days: float = None):
        """
        Initialize ingress finder.

        Args:
            precision_days: Precision for finding ingress time
        """
        self.precision = precision_days or self.DEFAULT_PRECISION

    def _get_sign_index(self, longitude: float) -> int:
        """Get sign index (0-11) from longitude."""
        return int(longitude / 30) % 12

    def find_ingresses(
        self,
        body: str,
        start_jd: float,
        end_jd: float,
    ) -> list[IngressEvent]:
        """
        Find all sign ingresses for a body within a date range.

        Args:
            body: Body name
            start_jd: Start Julian Day
            end_jd: End Julian Day

        Returns:
            List of IngressEvent objects
        """
        ingresses = []
        current_jd = start_jd

        prev_sign_idx = None
        prev_lon = None

        while current_jd < end_jd:
            pos = get_position(body, current_jd)
            lon = pos.longitude_decimal
            sign_idx = self._get_sign_index(lon)

            if prev_sign_idx is not None:
                # Check for sign change
                sign_changed = sign_idx != prev_sign_idx

                # Handle wrap-around (Pisces -> Aries)
                if abs(lon - prev_lon) > 180:
                    sign_changed = True

                if sign_changed:
                    # Find exact ingress time
                    ingress_jd = self._bisect_to_ingress(
                        body, current_jd - self.SCAN_STEP, current_jd
                    )

                    if ingress_jd:
                        ingress_pos = get_position(body, ingress_jd)

                        # Determine direction
                        is_retrograde = ingress_pos.speed_longitude < 0

                        # Get from/to signs
                        # For retrograde, the signs are reversed
                        if is_retrograde:
                            to_sign = ZODIAC_SIGNS[prev_sign_idx]
                            from_sign = ZODIAC_SIGNS[sign_idx]
                        else:
                            from_sign = ZODIAC_SIGNS[prev_sign_idx]
                            to_sign = ZODIAC_SIGNS[sign_idx]

                        event = IngressEvent(
                            jd=ingress_jd,
                            datetime_utc=jd_to_datetime(ingress_jd),
                            body=body,
                            from_sign=from_sign,
                            to_sign=to_sign,
                            longitude_exact=ingress_pos.longitude_decimal,
                            is_retrograde=is_retrograde,
                        )
                        ingresses.append(event)

            prev_sign_idx = sign_idx
            prev_lon = lon
            current_jd += self.SCAN_STEP

        return ingresses

    def _bisect_to_ingress(
        self,
        body: str,
        jd_start: float,
        jd_end: float,
    ) -> Optional[float]:
        """
        Use bisection to find exact ingress time.

        Finds when longitude crosses a sign boundary (multiple of 30°).
        """
        lon_start = get_position(body, jd_start).longitude_decimal
        lon_end = get_position(body, jd_end).longitude_decimal

        # Determine which boundary was crossed
        sign_start = int(lon_start / 30)
        sign_end = int(lon_end / 30)

        # Handle wrap-around
        if abs(lon_end - lon_start) > 180:
            # Wrapped around 0°
            if lon_start > 180:
                target = 360 if lon_start > lon_end else 0
            else:
                target = 0
        else:
            # Normal case: find the boundary between signs
            if lon_end > lon_start:
                # Moving forward
                target = (sign_start + 1) * 30
            else:
                # Moving backward (retrograde)
                target = sign_end * 30
                if target == 0 and lon_start > 300:
                    target = 360

        # Bisection
        iterations = 0
        max_iterations = 50

        while (jd_end - jd_start) > self.precision and iterations < max_iterations:
            jd_mid = (jd_start + jd_end) / 2
            lon_mid = get_position(body, jd_mid).longitude_decimal

            # Calculate distances from target
            dist_start = self._signed_distance(lon_start, target)
            dist_mid = self._signed_distance(lon_mid, target)

            if dist_start * dist_mid < 0:
                jd_end = jd_mid
                lon_end = lon_mid
            else:
                jd_start = jd_mid
                lon_start = lon_mid

            iterations += 1

        return (jd_start + jd_end) / 2

    def _signed_distance(self, lon: float, target: float) -> float:
        """Calculate signed distance from longitude to target."""
        diff = lon - target
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return diff

    def find_all_ingresses(
        self,
        start_date: datetime,
        end_date: datetime,
        bodies: Optional[list] = None,
    ) -> list[IngressEvent]:
        """
        Find all ingresses for multiple bodies.

        Args:
            start_date: Start datetime
            end_date: End datetime
            bodies: List of bodies (default: all planets)

        Returns:
            List of IngressEvent objects, sorted by date
        """
        if bodies is None:
            bodies = [
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
            ]

        start_jd = datetime_to_jd(start_date)
        end_jd = datetime_to_jd(end_date)

        all_ingresses = []

        for body in bodies:
            ingresses = self.find_ingresses(body, start_jd, end_jd)
            all_ingresses.extend(ingresses)

        # Sort by date
        all_ingresses.sort(key=lambda i: i.jd)

        return all_ingresses

    def find_sign_entries(
        self,
        body: str,
        sign: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[IngressEvent]:
        """
        Find all entries into a specific sign.

        Useful for tracking when a planet enters a particular sign.
        """
        all_ingresses = self.find_ingresses(
            body, datetime_to_jd(start_date), datetime_to_jd(end_date)
        )

        return [i for i in all_ingresses if i.to_sign == sign]


# Module-level convenience instance
_finder = IngressFinder()


def find_ingresses(
    body: str,
    start_date: datetime,
    end_date: datetime,
) -> list[IngressEvent]:
    """Find sign ingresses for a body."""
    start_jd = datetime_to_jd(start_date)
    end_jd = datetime_to_jd(end_date)
    return _finder.find_ingresses(body, start_jd, end_jd)


def find_all_ingresses(
    start_date: datetime,
    end_date: datetime,
    bodies: Optional[list] = None,
) -> list[IngressEvent]:
    """Find all ingresses for multiple bodies."""
    return _finder.find_all_ingresses(start_date, end_date, bodies)
