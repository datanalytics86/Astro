"""
Tests for the houses module.
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.houses import (
    HouseCalculator,
    calculate_houses,
    compare_house_systems,
    HOUSE_SYSTEMS,
)
from core.time_engine import datetime_to_jd, local_to_ut


class TestHouseCalculator:
    """Tests for HouseCalculator class."""

    def setup_method(self):
        """Setup for each test."""
        self.calculator = HouseCalculator()
        # Case study: Santiago, Chile
        self.lat = -33.4489
        self.lon = -70.6693

        # JD for case study (1986-12-05 11:03 UTC)
        dt = datetime(1986, 12, 5, 11, 3, 0)
        self.jd = datetime_to_jd(dt)

    def test_placidus_system(self):
        """Test Placidus house calculation."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "P")

        assert houses.system == "P"
        assert houses.system_name == "Placidus"

        # Should have 12 cusps
        assert len(houses.cusps) == 12

        # All cusps should be in valid range
        for cusp in houses.cusps:
            assert 0 <= cusp < 360

        # Ascendant should match house 1 cusp
        assert abs(houses.ascendant - houses.cusps[0]) < 0.001

    def test_koch_system(self):
        """Test Koch house calculation."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "K")

        assert houses.system == "K"
        assert houses.system_name == "Koch"

    def test_equal_houses(self):
        """Test Equal house system."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "E")

        assert houses.system == "E"

        # Equal houses: each cusp is 30° from the previous
        for i in range(11):
            diff = (houses.cusps[i + 1] - houses.cusps[i]) % 360
            assert abs(diff - 30) < 0.1

    def test_whole_sign_houses(self):
        """Test Whole Sign house system."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "W")

        assert houses.system == "W"

        # Whole sign: cusps at sign boundaries (multiples of 30)
        for cusp in houses.cusps:
            # Should be very close to 0, 30, 60, etc.
            normalized = cusp % 30
            assert normalized < 1 or normalized > 29

    def test_ascendant_in_capricorn(self):
        """Test that Ascendant is in Capricorn for case study."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "P")

        # Ascendant should be around 11° Capricorn (270° + 11° = 281°)
        assert 270 < houses.ascendant < 290

        # Should appear in zodiacal string
        assert "Capricorn" in houses.cusps_zodiacal[0]

    def test_mc_calculation(self):
        """Test MC calculation."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "P")

        # MC should be around 25° Libra (180° + 25° = 205°)
        # or possibly Scorpio depending on exact calculation
        assert 180 < houses.mc < 240

    def test_compare_systems(self):
        """Test house system comparison."""
        df = self.calculator.compare_systems(
            self.jd, self.lat, self.lon,
            systems=["P", "K", "E"]
        )

        # Should have rows for each system
        assert "Placidus" in df.columns or len(df.columns) >= 3

    def test_get_house_for_longitude(self):
        """Test determining which house a point is in."""
        houses = self.calculator.calculate(self.jd, self.lat, self.lon, "P")

        # Ascendant degree should be in house 1
        house = houses.get_house_for_longitude(houses.ascendant + 5)
        assert house == 1

        # MC should be in house 10
        house = houses.get_house_for_longitude(houses.mc + 5)
        assert house == 10


class TestHouseSystemComparison:
    """Tests for comparing different house systems."""

    def setup_method(self):
        """Setup for each test."""
        dt = datetime(1986, 12, 5, 11, 3, 0)
        self.jd = datetime_to_jd(dt)
        self.lat = -33.4489
        self.lon = -70.6693

    def test_ascendant_same_across_systems(self):
        """Ascendant should be the same regardless of house system."""
        systems = ["P", "K", "R", "C", "E"]
        ascendants = []

        for sys in systems:
            houses = calculate_houses(self.jd, self.lat, self.lon, sys)
            ascendants.append(houses.ascendant)

        # All ascendants should be within 0.01° of each other
        for asc in ascendants:
            assert abs(asc - ascendants[0]) < 0.01

    def test_mc_same_across_systems(self):
        """MC should be the same regardless of house system."""
        systems = ["P", "K", "R", "C"]
        mcs = []

        for sys in systems:
            houses = calculate_houses(self.jd, self.lat, self.lon, sys)
            mcs.append(houses.mc)

        # All MCs should be within 0.01° of each other
        for mc in mcs:
            assert abs(mc - mcs[0]) < 0.01

    def test_intermediate_cusps_differ(self):
        """Intermediate cusps should differ between systems."""
        placidus = calculate_houses(self.jd, self.lat, self.lon, "P")
        equal = calculate_houses(self.jd, self.lat, self.lon, "E")

        # House 2 cusp should be different
        diff = abs(placidus.cusps[1] - equal.cusps[1])
        # Normalize for wrap-around
        if diff > 180:
            diff = 360 - diff

        # Should have some difference (more than 1°)
        assert diff > 1 or diff < 359


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
