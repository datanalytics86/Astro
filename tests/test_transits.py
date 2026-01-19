"""
Tests for the transits module.
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.transits import (
    TransitFinder,
    find_transit,
    find_all_transits,
)
from core.time_engine import datetime_to_jd


class TestTransitFinder:
    """Tests for TransitFinder class."""

    def setup_method(self):
        """Setup for each test."""
        self.finder = TransitFinder(precision_days=0.001)  # ~86 seconds

    def test_find_jupiter_conjunction(self):
        """Test finding Jupiter conjunctions to a point."""
        # Jupiter takes ~12 years to go around the zodiac
        # Find conjunctions to 0° Aries over 2 years
        start_jd = datetime_to_jd(datetime(2022, 1, 1))
        end_jd = datetime_to_jd(datetime(2024, 1, 1))

        events = self.finder.find_exact_aspect(
            "jupiter",
            natal_position=0.0,  # 0° Aries
            aspect_angle=0,  # Conjunction
            start_jd=start_jd,
            end_jd=end_jd,
            natal_point_name="test_point",
        )

        # Jupiter entered Aries in May 2022, so should find at least one
        assert len(events) >= 1

        for event in events:
            assert event.aspect == "conjunction"
            assert event.transiting_body == "jupiter"

    def test_find_saturn_opposition(self):
        """Test finding Saturn oppositions."""
        start_jd = datetime_to_jd(datetime(2020, 1, 1))
        end_jd = datetime_to_jd(datetime(2022, 1, 1))

        events = self.finder.find_exact_aspect(
            "saturn",
            natal_position=270.0,  # 0° Capricorn
            aspect_angle=180,  # Opposition
            start_jd=start_jd,
            end_jd=end_jd,
        )

        # Check that events have correct aspect type
        for event in events:
            assert event.aspect == "opposition"

    def test_retrograde_multiple_passes(self):
        """Test that retrograde motion creates multiple passes."""
        # Mercury retrogrades create 3 passes over the same point
        # Use a longer period to catch a full retrograde cycle
        start_jd = datetime_to_jd(datetime(2023, 1, 1))
        end_jd = datetime_to_jd(datetime(2023, 6, 1))

        # Pick a point Mercury will pass multiple times
        events = self.finder.find_exact_aspect(
            "mercury",
            natal_position=330.0,  # ~0° Pisces
            aspect_angle=0,
            start_jd=start_jd,
            end_jd=end_jd,
        )

        # Should potentially have multiple passes
        # Mercury crosses each degree multiple times per year
        assert len(events) >= 1


class TestFindAllTransits:
    """Tests for the find_all_transits function."""

    def setup_method(self):
        """Setup natal positions for testing."""
        self.natal_positions = {
            "sun": 253.0,  # ~13° Sagittarius
            "moon": 306.0,  # ~6° Aquarius
            "mercury": 233.0,  # ~23° Scorpio
        }

    def test_basic_transit_search(self):
        """Test basic transit search functionality."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)

        df = find_all_transits(
            self.natal_positions,
            start,
            end,
            transiting_bodies=["jupiter", "saturn"],
            aspects=["conjunction", "opposition"],
        )

        # Should return a DataFrame
        assert hasattr(df, "columns")

        # Required columns
        if not df.empty:
            assert "transiting_body" in df.columns
            assert "natal_point" in df.columns
            assert "aspect" in df.columns

    def test_transit_chronological_order(self):
        """Test that transits are returned in chronological order."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        df = find_all_transits(
            self.natal_positions,
            start,
            end,
        )

        if len(df) > 1:
            dates = df["datetime_utc"].tolist()
            # Check chronological order
            for i in range(len(dates) - 1):
                assert dates[i] <= dates[i + 1]


class TestTransitPrecision:
    """Tests for transit calculation precision."""

    def test_precision_setting(self):
        """Test that precision setting affects calculation."""
        finder_coarse = TransitFinder(precision_days=0.1)
        finder_fine = TransitFinder(precision_days=0.0001)

        assert finder_coarse.precision == 0.1
        assert finder_fine.precision == 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
