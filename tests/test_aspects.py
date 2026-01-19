"""
Tests for the aspects module.
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.aspects import (
    AspectEngine,
    find_aspect,
    find_all_aspects,
    aspect_matrix,
    calculate_aspect_summary,
    ASPECTS,
)


class TestAspectEngine:
    """Tests for AspectEngine class."""

    def setup_method(self):
        """Setup for each test."""
        self.engine = AspectEngine()

    def test_calculate_angle_simple(self):
        """Test angle calculation for simple cases."""
        # Same position = 0°
        assert self.engine.calculate_angle(0, 0) == 0

        # Opposite positions = 180°
        assert self.engine.calculate_angle(0, 180) == 180

        # 90° apart
        assert self.engine.calculate_angle(0, 90) == 90
        assert self.engine.calculate_angle(90, 0) == 90

    def test_calculate_angle_wraparound(self):
        """Test angle calculation across 0°/360° boundary."""
        # 350° to 10° = 20° apart
        assert self.engine.calculate_angle(350, 10) == 20

        # 10° to 350° = same
        assert self.engine.calculate_angle(10, 350) == 20

    def test_find_conjunction(self):
        """Test conjunction detection."""
        # Exact conjunction
        result = self.engine.find_aspect(100, 100)
        assert result is not None
        assert result.aspect_name == "conjunction"
        assert result.orb < 0.01

        # Within orb conjunction
        result = self.engine.find_aspect(100, 105)
        assert result is not None
        assert result.aspect_name == "conjunction"
        assert abs(result.orb - 5) < 0.01

        # Outside orb (> 8°)
        result = self.engine.find_aspect(100, 110)
        assert result is None or result.aspect_name != "conjunction"

    def test_find_opposition(self):
        """Test opposition detection."""
        # Exact opposition
        result = self.engine.find_aspect(0, 180)
        assert result is not None
        assert result.aspect_name == "opposition"
        assert result.orb < 0.01

        # Within orb
        result = self.engine.find_aspect(0, 175)
        assert result is not None
        assert result.aspect_name == "opposition"

    def test_find_trine(self):
        """Test trine detection."""
        # Exact trine (120°)
        result = self.engine.find_aspect(0, 120)
        assert result is not None
        assert result.aspect_name == "trine"

        result = self.engine.find_aspect(0, 240)  # Also 120° apart
        assert result is not None
        assert result.aspect_name == "trine"

    def test_find_square(self):
        """Test square detection."""
        # 90° aspect
        result = self.engine.find_aspect(0, 90)
        assert result is not None
        assert result.aspect_name == "square"

        result = self.engine.find_aspect(0, 270)  # Also 90° apart
        assert result is not None
        assert result.aspect_name == "square"

    def test_find_sextile(self):
        """Test sextile detection."""
        # 60° aspect
        result = self.engine.find_aspect(0, 60)
        assert result is not None
        assert result.aspect_name == "sextile"

    def test_applying_separating(self):
        """Test applying/separating detection."""
        # Planet 1 at 100°, speed +1°/day
        # Planet 2 at 105°, speed +0.5°/day
        # Planet 1 is catching up = applying conjunction
        result = self.engine.find_aspect(100, 105, 1.0, 0.5, "p1", "p2")
        assert result is not None
        assert result.is_applying == True

        # Reverse speeds = separating
        result = self.engine.find_aspect(100, 105, 0.5, 1.0, "p1", "p2")
        assert result is not None
        assert result.is_separating == True

    def test_orb_strength(self):
        """Test that tighter orbs give higher strength."""
        # Exact aspect = strength 1.0
        result = self.engine.find_aspect(0, 0)
        assert result.strength > 0.99

        # Half orb = strength ~0.5
        result = self.engine.find_aspect(0, 4)  # 4° orb for 8° max
        assert 0.4 < result.strength < 0.6


class TestAspectFinding:
    """Tests for finding aspects in chart data."""

    def setup_method(self):
        """Setup test positions."""
        self.positions = {
            "sun": {"longitude_decimal": 253.0, "speed_longitude": 1.0},
            "moon": {"longitude_decimal": 306.0, "speed_longitude": 13.0},
            "mercury": {"longitude_decimal": 233.0, "speed_longitude": 1.5},
            "venus": {"longitude_decimal": 216.0, "speed_longitude": 1.2},
            "mars": {"longitude_decimal": 348.0, "speed_longitude": 0.6},
        }

    def test_find_all_aspects(self):
        """Test finding all aspects in a set of positions."""
        aspects = find_all_aspects(self.positions)

        # Should find some aspects
        assert len(aspects) > 0

        # All aspects should have required fields
        for asp in aspects:
            assert asp.body1 in self.positions
            assert asp.body2 in self.positions
            assert asp.aspect_name in ASPECTS
            assert 0 <= asp.orb <= 10

    def test_aspect_matrix(self):
        """Test aspect matrix generation."""
        matrix = aspect_matrix(self.positions)

        # Should be a DataFrame
        assert hasattr(matrix, "loc")

        # Should have bodies as both index and columns
        for body in self.positions.keys():
            assert body in matrix.index
            assert body in matrix.columns

    def test_aspect_summary(self):
        """Test aspect summary calculation."""
        aspects = find_all_aspects(self.positions)
        summary = calculate_aspect_summary(aspects)

        assert "total" in summary
        assert "major" in summary
        assert "minor" in summary
        assert "by_type" in summary

        assert summary["total"] == len(aspects)


class TestMinorAspects:
    """Tests for minor aspect detection."""

    def setup_method(self):
        """Setup for each test."""
        self.engine = AspectEngine(include_minor=True)

    def test_quincunx(self):
        """Test quincunx (150°) detection."""
        result = self.engine.find_aspect(0, 150)
        assert result is not None
        assert result.aspect_name == "quincunx"

    def test_semisextile(self):
        """Test semisextile (30°) detection."""
        result = self.engine.find_aspect(0, 30)
        assert result is not None
        assert result.aspect_name == "semisextile"

    def test_semisquare(self):
        """Test semisquare (45°) detection."""
        result = self.engine.find_aspect(0, 45)
        assert result is not None
        assert result.aspect_name == "semisquare"

    def test_exclude_minor(self):
        """Test excluding minor aspects."""
        engine = AspectEngine(include_minor=False)

        # Quincunx should not be found
        result = engine.find_aspect(0, 150)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
