"""
Tests for the time_engine module.
"""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.time_engine import (
    TimeEngine,
    datetime_to_jd,
    jd_to_datetime,
    get_delta_t,
    get_timezone_for_location,
)


class TestTimeEngine:
    """Tests for TimeEngine class."""

    def setup_method(self):
        """Setup for each test."""
        self.engine = TimeEngine()

    def test_datetime_to_jd_known_value(self):
        """Test JD calculation against known value."""
        # J2000.0 epoch: 2000-01-01 12:00:00 TT = JD 2451545.0
        # UTC is approximately the same at this epoch
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = datetime_to_jd(dt)

        # Should be very close to 2451545.0
        assert abs(jd - 2451545.0) < 0.001

    def test_jd_to_datetime_roundtrip(self):
        """Test that JD conversion round-trips correctly."""
        original = datetime(1986, 12, 5, 11, 3, 0, tzinfo=timezone.utc)
        jd = datetime_to_jd(original)
        recovered = jd_to_datetime(jd)

        assert abs((recovered - original).total_seconds()) < 1

    def test_delta_t_1986(self):
        """Test Delta-T for 1986."""
        delta_t = get_delta_t(1986, 12)

        # Delta-T in 1986 was approximately 54 seconds
        assert 50 < delta_t < 58

    def test_delta_t_2000(self):
        """Test Delta-T for 2000."""
        delta_t = get_delta_t(2000, 1)

        # Delta-T in 2000 was approximately 63-64 seconds
        assert 60 < delta_t < 68

    def test_delta_t_historical(self):
        """Test Delta-T for historical date."""
        delta_t = get_delta_t(1800, 1)

        # Delta-T in 1800 was approximately 13-14 seconds
        assert 10 < delta_t < 18

    def test_local_to_ut_santiago(self):
        """Test conversion for Santiago, Chile."""
        dt = datetime(1986, 12, 5, 8, 3, 0)  # Naive local time
        result = self.engine.local_to_ut(
            dt,
            "America/Santiago",
            lat=-33.4489,
            lon=-70.6693,
        )

        # UTC should be 3 hours ahead (Chile summer time)
        assert result.utc.hour == 11
        assert result.utc.day == 5
        assert result.utc.month == 12
        assert result.utc.year == 1986

        # Check DST detection
        assert result.dst_active == True  # December = summer in Chile

    def test_timezone_lookup(self):
        """Test timezone lookup for coordinates."""
        # Santiago, Chile
        tz = get_timezone_for_location(-33.4489, -70.6693)
        assert tz == "America/Santiago"

        # New York
        tz = get_timezone_for_location(40.7128, -74.0060)
        assert tz == "America/New_York"

    def test_sidereal_time(self):
        """Test sidereal time calculation."""
        # At J2000.0, GMST should be approximately 280.46°
        jd = 2451545.0
        gmst = self.engine.get_sidereal_time(jd, longitude=0.0)

        assert abs(gmst - 280.46) < 1.0

    def test_obliquity_j2000(self):
        """Test obliquity calculation at J2000."""
        jd_tt = 2451545.0
        obliquity = self.engine.get_obliquity(jd_tt)

        # Mean obliquity at J2000 is about 23.439°
        assert abs(obliquity - 23.439) < 0.01


class TestJulianDayEdgeCases:
    """Test edge cases in Julian Day calculations."""

    def test_jd_negative_year(self):
        """Test JD calculation for dates BCE."""
        # Not directly testing BCE, but ensuring algorithm handles it
        dt = datetime(1, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = datetime_to_jd(dt)

        # JD for 0001-01-01 12:00 should be approximately 1721424
        assert 1721420 < jd < 1721430

    def test_jd_far_future(self):
        """Test JD calculation for far future date."""
        dt = datetime(3000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = datetime_to_jd(dt)

        # Should be a large positive number
        assert jd > 2816787


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
