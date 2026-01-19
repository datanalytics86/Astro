"""
Tests for the ephemeris module.
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ephemeris import (
    EphemerisEngine,
    get_position,
    get_all_positions,
    get_lunar_phase,
    BODY_MAP,
)
from core.time_engine import datetime_to_jd


class TestEphemerisEngine:
    """Tests for EphemerisEngine class."""

    def setup_method(self):
        """Setup for each test."""
        self.engine = EphemerisEngine()

    def test_get_sun_position(self):
        """Test Sun position calculation."""
        # Test for a known date
        dt = datetime(1986, 12, 5, 11, 3, 0)  # UTC
        jd = datetime_to_jd(dt)

        pos = self.engine.get_position("sun", jd)

        # Sun should be in Sagittarius in early December
        assert pos.zodiac_sign == "Sagittarius"
        # Approximately 13° Sagittarius (240° + 13° = 253°)
        assert 250 < pos.longitude_decimal < 260

        # Sun is never retrograde
        assert pos.is_retrograde == False

        # Sun's speed should be around 1°/day
        assert 0.9 < pos.speed_longitude < 1.1

    def test_get_moon_position(self):
        """Test Moon position calculation."""
        dt = datetime(1986, 12, 5, 11, 3, 0)
        jd = datetime_to_jd(dt)

        pos = self.engine.get_position("moon", jd)

        # Moon should be in Aquarius (~6° Aquarius = 306°)
        assert pos.zodiac_sign == "Aquarius"
        assert 300 < pos.longitude_decimal < 315

        # Moon's speed should be around 12-15°/day
        assert 10 < abs(pos.speed_longitude) < 16

    def test_get_all_bodies(self):
        """Test calculation of all standard bodies."""
        dt = datetime(2000, 1, 1, 12, 0, 0)
        jd = datetime_to_jd(dt)

        positions = self.engine.get_all_positions(jd)

        # Should have all standard bodies
        assert "sun" in positions
        assert "moon" in positions
        assert "mercury" in positions
        assert "venus" in positions
        assert "mars" in positions
        assert "jupiter" in positions
        assert "saturn" in positions
        assert "uranus" in positions
        assert "neptune" in positions
        assert "pluto" in positions

    def test_longitude_range(self):
        """Test that all longitudes are in valid range."""
        dt = datetime(2020, 6, 21, 12, 0, 0)  # Summer solstice
        jd = datetime_to_jd(dt)

        positions = self.engine.get_all_positions(jd)

        for body, pos in positions.items():
            assert 0 <= pos.longitude_decimal < 360, f"{body} longitude out of range"

    def test_retrograde_detection(self):
        """Test retrograde detection (negative speed)."""
        # Mercury retrograde periods happen 3-4 times per year
        # Test a known Mercury retrograde: late January 2022
        dt = datetime(2022, 1, 25, 12, 0, 0)
        jd = datetime_to_jd(dt)

        pos = self.engine.get_position("mercury", jd)

        # Check that retrograde flag matches negative speed
        assert pos.is_retrograde == (pos.speed_longitude < 0)

    def test_zodiacal_string_format(self):
        """Test zodiacal position string format."""
        dt = datetime(2000, 1, 1, 12, 0, 0)
        jd = datetime_to_jd(dt)

        pos = self.engine.get_position("sun", jd)

        # Zodiacal string should contain sign name
        assert any(sign in pos.longitude_zodiacal for sign in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ])

        # Should contain degree symbol
        assert "°" in pos.longitude_zodiacal


class TestLunarPhase:
    """Tests for lunar phase calculation."""

    def test_new_moon(self):
        """Test detection of new moon."""
        # Known new moon: January 13, 2021
        dt = datetime(2021, 1, 13, 5, 0, 0)  # Approximately
        jd = datetime_to_jd(dt)

        phase = get_lunar_phase(jd)

        # Phase angle should be near 0
        assert phase["phase_angle"] < 30 or phase["phase_angle"] > 330
        assert "New" in phase["phase_name"]

    def test_full_moon(self):
        """Test detection of full moon."""
        # Known full moon: January 28, 2021
        dt = datetime(2021, 1, 28, 19, 0, 0)  # Approximately
        jd = datetime_to_jd(dt)

        phase = get_lunar_phase(jd)

        # Phase angle should be near 180
        assert 150 < phase["phase_angle"] < 210
        assert "Full" in phase["phase_name"]

    def test_waxing_flag(self):
        """Test waxing moon detection."""
        # A few days after new moon should be waxing
        dt = datetime(2021, 1, 18, 12, 0, 0)
        jd = datetime_to_jd(dt)

        phase = get_lunar_phase(jd)

        assert phase["is_waxing"] == True


class TestCaseStudyValidation:
    """Validation tests for the case study date (1986-12-05 08:03 Santiago)."""

    def setup_method(self):
        """Setup with case study Julian Day."""
        # 1986-12-05 11:03:00 UTC (08:03 Santiago = UTC-3)
        self.dt = datetime(1986, 12, 5, 11, 3, 0)
        self.jd = datetime_to_jd(self.dt)
        self.engine = EphemerisEngine()

    def test_sun_position_case_study(self):
        """Verify Sun position for case study."""
        pos = self.engine.get_position("sun", self.jd)

        # Sun should be around 13° Sagittarius
        assert pos.zodiac_sign == "Sagittarius"
        assert 10 < pos.zodiac_degree < 16

    def test_moon_position_case_study(self):
        """Verify Moon position for case study."""
        pos = self.engine.get_position("moon", self.jd)

        # Moon should be around 6° Aquarius
        assert pos.zodiac_sign == "Aquarius"
        assert 3 < pos.zodiac_degree < 10

    def test_mercury_position_case_study(self):
        """Verify Mercury position for case study."""
        pos = self.engine.get_position("mercury", self.jd)

        # Mercury should be in Scorpio or early Sagittarius
        assert pos.zodiac_sign in ["Scorpio", "Sagittarius"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
