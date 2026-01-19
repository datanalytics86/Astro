"""
Time Engine Module - Precise astronomical time conversions.

This module handles the rigorous conversion between different time scales
used in astronomical calculations:
- Local time (with timezone)
- UTC (Coordinated Universal Time)
- UT1 (Universal Time, rotation-based)
- TT (Terrestrial Time, atomic time scale)
- TDB (Barycentric Dynamical Time, for planetary calculations)

The key relationship is:
TT = UTC + leap_seconds + 32.184s
TT = UT1 + Delta-T

Delta-T varies over time and must be computed from tables or models.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pytz
from timezonefinder import TimezoneFinder


@dataclass
class TimeResult:
    """Result of time conversion with all relevant time scales."""

    local: datetime
    utc: datetime
    jd_ut: float  # Julian Day UT
    jd_tt: float  # Julian Day Terrestrial Time
    jd_tdb: float  # Julian Day Barycentric Dynamical Time
    delta_t: float  # TT - UT1 in seconds
    timezone_offset_hours: float
    timezone_name: str
    dst_active: bool
    ut1_correction: float  # UT1 - UTC (usually small, from IERS)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "local": self.local.isoformat(),
            "utc": self.utc.isoformat(),
            "jd_ut": self.jd_ut,
            "jd_tt": self.jd_tt,
            "jd_tdb": self.jd_tdb,
            "delta_t_seconds": self.delta_t,
            "timezone_offset_hours": self.timezone_offset_hours,
            "timezone_name": self.timezone_name,
            "dst_active": self.dst_active,
            "ut1_correction": self.ut1_correction,
        }


class TimeEngine:
    """
    Precise time conversion engine for astronomical calculations.

    Handles timezone lookups, Julian Day calculations, and time scale
    conversions with proper handling of Delta-T.
    """

    # J2000.0 epoch in Julian Days
    J2000 = 2451545.0

    # Julian Day of Unix epoch (1970-01-01 00:00:00 UTC)
    JD_UNIX_EPOCH = 2440587.5

    def __init__(self):
        """Initialize the time engine."""
        self._tz_finder = TimezoneFinder()

    def get_timezone_for_location(self, lat: float, lon: float) -> str:
        """
        Get timezone string for a geographic location.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Timezone string (e.g., 'America/Santiago')
        """
        tz_name = self._tz_finder.timezone_at(lat=lat, lng=lon)
        if tz_name is None:
            # Fallback to UTC offset estimation
            offset_hours = round(lon / 15)
            if offset_hours >= 0:
                return f"Etc/GMT-{offset_hours}"
            else:
                return f"Etc/GMT+{-offset_hours}"
        return tz_name

    def local_to_ut(
        self,
        local_dt: datetime,
        timezone_str: str,
        lat: float,
        lon: float,
    ) -> TimeResult:
        """
        Convert local datetime to all astronomical time scales.

        Args:
            local_dt: Local datetime (naive or aware)
            timezone_str: Timezone string (e.g., 'America/Santiago')
            lat: Latitude in decimal degrees (for future UT1 corrections)
            lon: Longitude in decimal degrees

        Returns:
            TimeResult with all time scale conversions
        """
        # Get timezone
        tz = pytz.timezone(timezone_str)

        # Localize the datetime if naive
        if local_dt.tzinfo is None:
            local_aware = tz.localize(local_dt)
        else:
            local_aware = local_dt

        # Convert to UTC
        utc_dt = local_aware.astimezone(pytz.UTC)

        # Get timezone offset
        offset = local_aware.utcoffset()
        if offset:
            offset_hours = offset.total_seconds() / 3600
        else:
            offset_hours = 0.0

        # Check DST
        dst = local_aware.dst()
        dst_active = dst is not None and dst.total_seconds() > 0

        # Calculate Julian Day (UT)
        jd_ut = self.datetime_to_jd(utc_dt)

        # Calculate Delta-T
        delta_t = self.calculate_delta_t(utc_dt.year, utc_dt.month)

        # UT1 - UTC correction (simplified, normally from IERS)
        # For historical dates, this is typically within ±0.9 seconds
        ut1_correction = 0.0  # Simplified; real implementation would query IERS

        # Calculate TT (Terrestrial Time)
        # TT = UT1 + Delta-T, where UT1 ≈ UTC + ut1_correction
        jd_tt = jd_ut + (delta_t + ut1_correction) / 86400.0

        # Calculate TDB (Barycentric Dynamical Time)
        # TDB ≈ TT + periodic terms (max ~1.7ms)
        jd_tdb = self.tt_to_tdb(jd_tt)

        return TimeResult(
            local=local_aware,
            utc=utc_dt,
            jd_ut=jd_ut,
            jd_tt=jd_tt,
            jd_tdb=jd_tdb,
            delta_t=delta_t,
            timezone_offset_hours=offset_hours,
            timezone_name=timezone_str,
            dst_active=dst_active,
            ut1_correction=ut1_correction,
        )

    def datetime_to_jd(self, dt: datetime) -> float:
        """
        Convert datetime to Julian Day.

        Uses the standard algorithm valid for dates after 4713 BC.
        The datetime should be in UTC.

        Args:
            dt: Datetime in UTC

        Returns:
            Julian Day number
        """
        # Ensure we have UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)

        year = dt.year
        month = dt.month
        day = dt.day

        # Add fractional day
        day_fraction = (
            dt.hour / 24.0
            + dt.minute / 1440.0
            + dt.second / 86400.0
            + dt.microsecond / 86400000000.0
        )

        # Julian Day algorithm (valid for Gregorian calendar)
        if month <= 2:
            year -= 1
            month += 12

        a = int(year / 100)
        b = 2 - a + int(a / 4)

        jd = (
            int(365.25 * (year + 4716))
            + int(30.6001 * (month + 1))
            + day
            + day_fraction
            + b
            - 1524.5
        )

        return jd

    def jd_to_datetime(self, jd: float) -> datetime:
        """
        Convert Julian Day to datetime (UTC).

        Args:
            jd: Julian Day number

        Returns:
            Datetime in UTC
        """
        # Algorithm from Meeus, "Astronomical Algorithms"
        jd = jd + 0.5
        z = int(jd)
        f = jd - z

        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - int(alpha / 4)

        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)

        day = b - d - int(30.6001 * e) + f

        if e < 14:
            month = e - 1
        else:
            month = e - 13

        if month > 2:
            year = c - 4716
        else:
            year = c - 4715

        # Extract time from fractional day
        day_int = int(day)
        day_frac = day - day_int

        hours = day_frac * 24
        hour = int(hours)
        minutes = (hours - hour) * 60
        minute = int(minutes)
        seconds = (minutes - minute) * 60
        second = int(seconds)
        microsecond = int((seconds - second) * 1000000)

        return datetime(
            year, month, day_int, hour, minute, second, microsecond, tzinfo=timezone.utc
        )

    def calculate_delta_t(self, year: int, month: int) -> float:
        """
        Calculate Delta-T (TT - UT1) for a given date.

        Uses polynomial expressions from various sources for different epochs.
        Uncertainty increases for dates far from the present.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Delta-T in seconds
        """
        # Decimal year
        y = year + (month - 0.5) / 12

        # Different expressions for different epochs
        # Based on Morrison & Stephenson (2004) and IERS data

        if year < -500:
            # Before -500
            u = (y - 1820) / 100
            return -20 + 32 * u * u

        elif year < 500:
            # -500 to 500
            u = y / 100
            return (
                10583.6
                - 1014.41 * u
                + 33.78311 * u**2
                - 5.952053 * u**3
                - 0.1798452 * u**4
                + 0.022174192 * u**5
                + 0.0090316521 * u**6
            )

        elif year < 1600:
            # 500 to 1600
            u = (y - 1000) / 100
            return (
                1574.2
                - 556.01 * u
                + 71.23472 * u**2
                + 0.319781 * u**3
                - 0.8503463 * u**4
                - 0.005050998 * u**5
                + 0.0083572073 * u**6
            )

        elif year < 1700:
            # 1600 to 1700
            t = y - 1600
            return 120 - 0.9808 * t - 0.01532 * t**2 + t**3 / 7129

        elif year < 1800:
            # 1700 to 1800
            t = y - 1700
            return (
                8.83
                + 0.1603 * t
                - 0.0059285 * t**2
                + 0.00013336 * t**3
                - t**4 / 1174000
            )

        elif year < 1860:
            # 1800 to 1860
            t = y - 1800
            return (
                13.72
                - 0.332447 * t
                + 0.0068612 * t**2
                + 0.0041116 * t**3
                - 0.00037436 * t**4
                + 0.0000121272 * t**5
                - 0.0000001699 * t**6
                + 0.000000000875 * t**7
            )

        elif year < 1900:
            # 1860 to 1900
            t = y - 1860
            return (
                7.62
                + 0.5737 * t
                - 0.251754 * t**2
                + 0.01680668 * t**3
                - 0.0004473624 * t**4
                + t**5 / 233174
            )

        elif year < 1920:
            # 1900 to 1920
            t = y - 1900
            return (
                -2.79
                + 1.494119 * t
                - 0.0598939 * t**2
                + 0.0061966 * t**3
                - 0.000197 * t**4
            )

        elif year < 1941:
            # 1920 to 1941
            t = y - 1920
            return 21.20 + 0.84493 * t - 0.076100 * t**2 + 0.0020936 * t**3

        elif year < 1961:
            # 1941 to 1961
            t = y - 1950
            return 29.07 + 0.407 * t - t**2 / 233 + t**3 / 2547

        elif year < 1986:
            # 1961 to 1986
            t = y - 1975
            return 45.45 + 1.067 * t - t**2 / 260 - t**3 / 718

        elif year < 2005:
            # 1986 to 2005
            t = y - 2000
            return (
                63.86
                + 0.3345 * t
                - 0.060374 * t**2
                + 0.0017275 * t**3
                + 0.000651814 * t**4
                + 0.00002373599 * t**5
            )

        elif year < 2050:
            # 2005 to 2050
            t = y - 2000
            return 62.92 + 0.32217 * t + 0.005589 * t**2

        elif year < 2150:
            # 2050 to 2150
            return -20 + 32 * ((y - 1820) / 100) ** 2 - 0.5628 * (2150 - y)

        else:
            # After 2150
            u = (y - 1820) / 100
            return -20 + 32 * u * u

    def tt_to_tdb(self, jd_tt: float) -> float:
        """
        Convert Terrestrial Time to Barycentric Dynamical Time.

        TDB differs from TT by periodic terms with amplitude ~1.7ms.
        This uses the expression from Fairhead & Bretagnon (1990).

        Args:
            jd_tt: Julian Day in TT

        Returns:
            Julian Day in TDB
        """
        # Time in Julian centuries from J2000.0 (TT)
        t = (jd_tt - self.J2000) / 36525.0

        # Simplified expression (main terms only)
        # Full expression has hundreds of terms
        g = np.radians(357.53 + 35999.050 * t)  # Mean anomaly of Earth

        # TDB - TT in seconds
        dt = 0.001658 * np.sin(g) + 0.000014 * np.sin(2 * g)

        return jd_tt + dt / 86400.0

    def get_obliquity(self, jd_tt: float) -> float:
        """
        Calculate the mean obliquity of the ecliptic.

        Uses the IAU 2006 precession model.

        Args:
            jd_tt: Julian Day in TT

        Returns:
            Mean obliquity in degrees
        """
        # Julian centuries from J2000.0
        t = (jd_tt - self.J2000) / 36525.0

        # IAU 2006 expression for mean obliquity (arcseconds)
        epsilon = (
            84381.406
            - 46.836769 * t
            - 0.0001831 * t**2
            + 0.00200340 * t**3
            - 0.000000576 * t**4
            - 0.0000000434 * t**5
        )

        return epsilon / 3600.0  # Convert to degrees

    def get_sidereal_time(
        self, jd_ut: float, longitude: float = 0.0, apparent: bool = False
    ) -> float:
        """
        Calculate sidereal time.

        Args:
            jd_ut: Julian Day in UT
            longitude: Observer longitude in degrees (E positive)
            apparent: If True, return apparent sidereal time (includes nutation)

        Returns:
            Sidereal time in degrees (0-360)
        """
        # Julian centuries from J2000.0
        t = (jd_ut - self.J2000) / 36525.0

        # Mean sidereal time at Greenwich (degrees)
        gmst = (
            280.46061837
            + 360.98564736629 * (jd_ut - self.J2000)
            + 0.000387933 * t**2
            - t**3 / 38710000
        )

        # Add longitude for local sidereal time
        lst = gmst + longitude

        # Normalize to 0-360
        lst = lst % 360
        if lst < 0:
            lst += 360

        if apparent:
            # Add nutation in longitude (simplified)
            omega = np.radians(125.04 - 1934.136 * t)
            nutation = -0.00478 * np.sin(omega)
            obliquity = self.get_obliquity(jd_ut)
            lst += nutation * np.cos(np.radians(obliquity))

        return lst

    def format_jd(self, jd: float, precision: int = 6) -> str:
        """Format Julian Day with specified precision."""
        return f"{jd:.{precision}f}"

    @staticmethod
    def format_datetime(dt: datetime, include_tz: bool = True) -> str:
        """Format datetime for display."""
        if include_tz and dt.tzinfo:
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# Module-level convenience functions
_engine = TimeEngine()


def local_to_ut(
    local_dt: datetime,
    timezone_str: str,
    lat: float = 0.0,
    lon: float = 0.0,
) -> TimeResult:
    """Convert local datetime to universal time scales."""
    return _engine.local_to_ut(local_dt, timezone_str, lat, lon)


def datetime_to_jd(dt: datetime) -> float:
    """Convert datetime to Julian Day."""
    return _engine.datetime_to_jd(dt)


def jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to datetime."""
    return _engine.jd_to_datetime(jd)


def get_delta_t(year: int, month: int) -> float:
    """Get Delta-T for a given date."""
    return _engine.calculate_delta_t(year, month)


def get_timezone_for_location(lat: float, lon: float) -> str:
    """Get timezone for geographic coordinates."""
    return _engine.get_timezone_for_location(lat, lon)
