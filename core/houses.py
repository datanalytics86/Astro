"""
House Systems Module - Multiple house calculation systems.

This module provides house cusp calculations using various house systems.
Each system has different mathematical approaches and historical traditions.

Supported systems:
- Placidus (P): Time-based, most popular in modern Western astrology
- Koch (K): Place-based, popular in German-speaking countries
- Regiomontanus (R): Medieval rational houses
- Campanus (C): Prime vertical division
- Equal (E): 30° from Ascendant
- Whole Sign (W): Sign-based houses
- Alcabitius (B): Semi-arc based
- Morinus (M): Equatorial houses
- Topocentric (T): Polich-Page system
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import swisseph as swe

from data.symbols import get_zodiac_sign, longitude_to_dms, longitude_to_zodiacal


# House system codes for Swiss Ephemeris
HOUSE_SYSTEMS = {
    "P": "Placidus",
    "K": "Koch",
    "R": "Regiomontanus",
    "C": "Campanus",
    "E": "Equal",
    "W": "Whole Sign",
    "B": "Alcabitius",
    "M": "Morinus",
    "T": "Topocentric",
    "O": "Porphyry",
    "A": "Equal (Asc)",
    "X": "Meridian",
}


@dataclass
class HouseData:
    """House calculation results."""

    system: str
    system_name: str
    ascendant: float
    mc: float
    armc: float  # Right Ascension of MC
    vertex: float
    equatorial_ascendant: float
    cusps: list[float]  # 12 cusps, index 0 = house 1
    cusps_dms: list[str]
    cusps_zodiacal: list[str]
    obliquity: float
    svp: float  # Sidereal Vernal Point (for sidereal)
    latitude: float
    longitude: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "system": self.system,
            "system_name": self.system_name,
            "ascendant": self.ascendant,
            "ascendant_zodiacal": longitude_to_zodiacal(self.ascendant),
            "mc": self.mc,
            "mc_zodiacal": longitude_to_zodiacal(self.mc),
            "armc": self.armc,
            "vertex": self.vertex,
            "vertex_zodiacal": longitude_to_zodiacal(self.vertex),
            "equatorial_ascendant": self.equatorial_ascendant,
            "cusps": self.cusps,
            "cusps_dms": self.cusps_dms,
            "cusps_zodiacal": self.cusps_zodiacal,
            "obliquity": self.obliquity,
            "svp": self.svp,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    def get_house_for_longitude(self, longitude: float) -> int:
        """
        Determine which house a given longitude falls in.

        Args:
            longitude: Ecliptic longitude in degrees (0-360)

        Returns:
            House number (1-12)
        """
        # Normalize longitude
        longitude = longitude % 360

        for i in range(12):
            cusp_start = self.cusps[i]
            cusp_end = self.cusps[(i + 1) % 12]

            # Handle wrap-around at 0°
            if cusp_start > cusp_end:
                # Cusp spans 0° (e.g., 350° to 10°)
                if longitude >= cusp_start or longitude < cusp_end:
                    return i + 1
            else:
                if cusp_start <= longitude < cusp_end:
                    return i + 1

        # Default to house 12 if not found (shouldn't happen)
        return 12


class HouseCalculator:
    """
    House cusp calculator supporting multiple systems.

    Provides calculations for various house systems and comparison tools.
    """

    def __init__(self):
        """Initialize the house calculator."""
        pass

    def calculate(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        system: str = "P",
    ) -> HouseData:
        """
        Calculate house cusps for a given system.

        Args:
            jd_ut: Julian Day in UT
            latitude: Geographic latitude in degrees (N positive)
            longitude: Geographic longitude in degrees (E positive)
            system: House system code (default 'P' for Placidus)

        Returns:
            HouseData with all house information
        """
        if system not in HOUSE_SYSTEMS:
            raise ValueError(
                f"Unknown house system: {system}. "
                f"Valid systems: {list(HOUSE_SYSTEMS.keys())}"
            )

        # Convert system to bytes for Swiss Ephemeris
        system_byte = system.encode('ascii')

        # Calculate houses
        # Returns (cusps[13], ascmc[10])
        # cusps[0] is unused, cusps[1-12] are house cusps
        # ascmc contains: [Asc, MC, ARMC, Vertex, Equasc, Co-Asc, Polar-Asc, ...]
        cusps, ascmc = swe.houses(jd_ut, latitude, longitude, system_byte)

        # Extract house cusps (skip index 0)
        house_cusps = list(cusps[1:13])

        # Extract key points
        ascendant = ascmc[0]
        mc = ascmc[1]
        armc = ascmc[2]
        vertex = ascmc[3]
        equatorial_asc = ascmc[4]

        # Calculate obliquity for reference
        obliquity_data = swe.calc_ut(jd_ut, swe.ECL_NUT, 0)
        obliquity = obliquity_data[0][2]  # Mean obliquity

        # Format cusps
        cusps_dms = [longitude_to_dms(c) for c in house_cusps]
        cusps_zodiacal = [longitude_to_zodiacal(c, include_seconds=False) for c in house_cusps]

        return HouseData(
            system=system,
            system_name=HOUSE_SYSTEMS[system],
            ascendant=ascendant,
            mc=mc,
            armc=armc,
            vertex=vertex,
            equatorial_ascendant=equatorial_asc,
            cusps=house_cusps,
            cusps_dms=cusps_dms,
            cusps_zodiacal=cusps_zodiacal,
            obliquity=obliquity,
            svp=0.0,  # Would need sidereal calculation
            latitude=latitude,
            longitude=longitude,
        )

    def compare_systems(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        systems: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Compare house cusps across multiple systems.

        Args:
            jd_ut: Julian Day in UT
            latitude: Geographic latitude
            longitude: Geographic longitude
            systems: List of system codes (default: all main systems)

        Returns:
            DataFrame with cusps for each system
        """
        if systems is None:
            systems = ["P", "K", "R", "C", "E", "W", "B", "M", "T"]

        data = {}

        for sys in systems:
            try:
                houses = self.calculate(jd_ut, latitude, longitude, sys)
                system_name = HOUSE_SYSTEMS[sys]

                # Add cusps
                for i, cusp in enumerate(houses.cusps, 1):
                    col = f"House {i}"
                    if col not in data:
                        data[col] = {}
                    data[col][system_name] = longitude_to_zodiacal(cusp, include_seconds=False)

                # Add Ascendant and MC
                if "Ascendant" not in data:
                    data["Ascendant"] = {}
                data["Ascendant"][system_name] = longitude_to_zodiacal(
                    houses.ascendant, include_seconds=False
                )

                if "MC" not in data:
                    data["MC"] = {}
                data["MC"][system_name] = longitude_to_zodiacal(
                    houses.mc, include_seconds=False
                )

            except Exception as e:
                # Skip systems that fail (e.g., at extreme latitudes)
                pass

        # Create DataFrame
        df = pd.DataFrame(data)
        return df.T

    def calculate_houses_with_positions(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        system: str = "P",
        planet_positions: Optional[dict] = None,
    ) -> dict:
        """
        Calculate houses and assign planets to houses.

        Args:
            jd_ut: Julian Day in UT
            latitude: Geographic latitude
            longitude: Geographic longitude
            system: House system code
            planet_positions: Dictionary of planet positions (from ephemeris)

        Returns:
            Dictionary with houses and planet assignments
        """
        houses = self.calculate(jd_ut, latitude, longitude, system)

        result = {
            "houses": houses.to_dict(),
            "planet_houses": {},
        }

        if planet_positions:
            for planet, pos in planet_positions.items():
                if hasattr(pos, "longitude_decimal"):
                    lon = pos.longitude_decimal
                else:
                    lon = pos.get("longitude_decimal", pos.get("longitude", 0))

                house_num = houses.get_house_for_longitude(lon)
                result["planet_houses"][planet] = house_num

        return result

    @staticmethod
    def get_system_description(system: str) -> str:
        """
        Get a description of a house system.

        Args:
            system: House system code

        Returns:
            Description string
        """
        descriptions = {
            "P": (
                "Placidus: Divides the time it takes for a degree of the ecliptic "
                "to rise from the Ascendant to the MC into equal parts. Most popular "
                "system in modern Western astrology."
            ),
            "K": (
                "Koch: Based on the birthplace latitude, divides the semi-arc "
                "of the Ascendant into equal parts. Popular in German-speaking countries."
            ),
            "R": (
                "Regiomontanus: Projects house divisions from the celestial equator "
                "onto the ecliptic through the north and south points of the horizon."
            ),
            "C": (
                "Campanus: Divides the prime vertical (east-west circle through "
                "zenith) into equal 30° arcs, then projects onto the ecliptic."
            ),
            "E": (
                "Equal: Simply divides the ecliptic into twelve 30° houses "
                "starting from the Ascendant degree."
            ),
            "W": (
                "Whole Sign: Each house occupies one complete zodiac sign, "
                "with the 1st house being the entire sign containing the Ascendant."
            ),
            "B": (
                "Alcabitius: Medieval system dividing the semi-arc from Ascendant "
                "to MC into three equal parts on the celestial equator."
            ),
            "M": (
                "Morinus: Projects equatorial divisions directly onto the ecliptic "
                "without reference to the horizon. The Ascendant is not a house cusp."
            ),
            "T": (
                "Topocentric (Polich-Page): Designed for precise timing, based on "
                "the geographic location rather than geocentric perspective."
            ),
        }

        return descriptions.get(
            system,
            f"{HOUSE_SYSTEMS.get(system, 'Unknown')}: No detailed description available.",
        )


# Module-level convenience instance
_calculator = HouseCalculator()


def calculate_houses(
    jd_ut: float,
    latitude: float,
    longitude: float,
    system: str = "P",
) -> HouseData:
    """Calculate house cusps."""
    return _calculator.calculate(jd_ut, latitude, longitude, system)


def compare_house_systems(
    jd_ut: float,
    latitude: float,
    longitude: float,
    systems: Optional[list] = None,
) -> pd.DataFrame:
    """Compare house cusps across multiple systems."""
    return _calculator.compare_systems(jd_ut, latitude, longitude, systems)
