"""
Secondary Progressions Module - Day-for-a-year symbolic time.

Secondary progressions use the symbolic equivalence of one day = one year.
To find progressed positions for age N, calculate the planetary positions
for N days after birth.

This is the most commonly used progression system in Western astrology.

Features:
- Progressed planetary positions
- Progressed angles (MC, Ascendant)
- Progressed lunar phases
- Progressed aspects to natal
- Solar arc directions (alternative method)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from core.ephemeris import get_position, get_all_positions, EphemerisEngine
from core.houses import calculate_houses, HouseData
from core.aspects import find_all_aspects, AspectEngine, ASPECTS
from core.time_engine import datetime_to_jd, jd_to_datetime, local_to_ut, TimeEngine


@dataclass
class ProgressedPosition:
    """A single progressed planetary position."""

    body: str
    natal_longitude: float
    progressed_longitude: float
    movement: float  # Total degrees moved since birth
    annual_motion: float  # Average degrees per progressed year
    is_retrograde: bool
    zodiac_sign: str
    sign_changed: bool  # True if sign different from natal

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "body": self.body,
            "natal_longitude": self.natal_longitude,
            "progressed_longitude": self.progressed_longitude,
            "movement_degrees": self.movement,
            "annual_motion": self.annual_motion,
            "is_retrograde": self.is_retrograde,
            "zodiac_sign": self.zodiac_sign,
            "sign_changed": self.sign_changed,
        }


@dataclass
class ProgressedChart:
    """Complete progressed chart data."""

    target_date: datetime
    age_years: float
    progressed_date: datetime  # The "symbolic" date (birth + age days)
    jd_progressed: float

    # Positions
    positions: dict[str, ProgressedPosition]

    # Progressed angles
    progressed_mc: float
    progressed_asc: float
    natal_mc: float
    natal_asc: float

    # Progressed Moon data (most important in progressions)
    moon_phase_angle: float
    moon_phase_name: str
    moon_natal_aspects: list

    # Aspects to natal
    progressed_to_natal_aspects: list

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "target_date": self.target_date.isoformat(),
            "age_years": self.age_years,
            "progressed_date": self.progressed_date.isoformat(),
            "jd_progressed": self.jd_progressed,
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
            "progressed_mc": self.progressed_mc,
            "progressed_asc": self.progressed_asc,
            "natal_mc": self.natal_mc,
            "natal_asc": self.natal_asc,
            "moon_phase_angle": self.moon_phase_angle,
            "moon_phase_name": self.moon_phase_name,
            "progressed_to_natal_aspects": [
                a.to_dict() if hasattr(a, 'to_dict') else a
                for a in self.progressed_to_natal_aspects
            ],
        }


@dataclass
class ProgressedLunarPhase:
    """Progressed lunar phase information."""

    date: datetime
    age_years: float
    phase_angle: float
    phase_name: str
    sun_longitude: float
    moon_longitude: float
    is_new_moon: bool
    is_full_moon: bool

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "date": self.date.isoformat(),
            "age_years": self.age_years,
            "phase_angle": self.phase_angle,
            "phase_name": self.phase_name,
            "sun_longitude": self.sun_longitude,
            "moon_longitude": self.moon_longitude,
            "is_new_moon": self.is_new_moon,
            "is_full_moon": self.is_full_moon,
        }


class SecondaryProgressions:
    """
    Calculate secondary progressions (day-for-a-year).

    The fundamental principle: positions N days after birth
    represent the progressed chart for age N years.
    """

    # Zodiac signs for reference
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    def __init__(self):
        """Initialize progressions calculator."""
        self.ephemeris = EphemerisEngine()
        self.aspect_engine = AspectEngine()

    def _get_sign(self, longitude: float) -> str:
        """Get zodiac sign from longitude."""
        index = int(longitude / 30) % 12
        return self.SIGNS[index]

    def calculate_progressed_date(
        self,
        birth_date: datetime,
        target_date: datetime,
    ) -> tuple[datetime, float]:
        """
        Calculate the progressed date for a target date.

        Args:
            birth_date: Birth datetime
            target_date: Date to progress to

        Returns:
            Tuple of (progressed_datetime, age_in_years)
        """
        # Calculate age in years (precise)
        delta = target_date - birth_date
        age_years = delta.days / 365.25

        # Progressed date = birth + age_years days
        progressed_delta = timedelta(days=age_years)
        progressed_date = birth_date + progressed_delta

        return progressed_date, age_years

    def calculate_progressed_chart(
        self,
        birth_datetime: datetime,
        birth_latitude: float,
        birth_longitude: float,
        target_date: datetime,
        timezone: str = "UTC",
        house_system: str = "P",
    ) -> ProgressedChart:
        """
        Calculate complete progressed chart for a target date.

        Args:
            birth_datetime: Birth datetime (local time)
            birth_latitude: Birth latitude
            birth_longitude: Birth longitude
            target_date: Date to calculate progressions for
            timezone: Birth timezone
            house_system: House system for angles

        Returns:
            ProgressedChart with all progressed data
        """
        # Convert birth time
        time_result = local_to_ut(
            birth_datetime, timezone, birth_latitude, birth_longitude
        )
        natal_jd = time_result.jd_tt

        # Get natal positions
        natal_positions = get_all_positions(natal_jd)
        natal_houses = calculate_houses(
            time_result.jd_ut, birth_latitude, birth_longitude, house_system
        )

        # Calculate progressed date
        progressed_date, age_years = self.calculate_progressed_date(
            birth_datetime, target_date
        )
        progressed_jd = natal_jd + age_years  # Add age as days

        # Get progressed positions
        progressed_raw = get_all_positions(progressed_jd)

        # Calculate progressed positions with comparison to natal
        progressed_positions = {}
        for body in natal_positions:
            if body not in progressed_raw:
                continue

            natal_pos = natal_positions[body]
            prog_pos = progressed_raw[body]

            natal_lon = natal_pos.longitude_decimal
            prog_lon = prog_pos.longitude_decimal

            # Calculate movement (accounting for wrap-around)
            movement = prog_lon - natal_lon
            if movement < -180:
                movement += 360
            elif movement > 180:
                movement -= 360

            annual_motion = movement / age_years if age_years > 0 else 0

            progressed_positions[body] = ProgressedPosition(
                body=body,
                natal_longitude=natal_lon,
                progressed_longitude=prog_lon,
                movement=movement,
                annual_motion=annual_motion,
                is_retrograde=prog_pos.is_retrograde,
                zodiac_sign=self._get_sign(prog_lon),
                sign_changed=self._get_sign(prog_lon) != self._get_sign(natal_lon),
            )

        # Calculate progressed angles using solar arc
        # MC progresses approximately 1° per year (like Sun)
        sun_movement = progressed_positions["sun"].movement if "sun" in progressed_positions else age_years
        progressed_mc = (natal_houses.mc + sun_movement) % 360
        progressed_asc = (natal_houses.ascendant + sun_movement) % 360

        # Calculate progressed lunar phase
        if "sun" in progressed_positions and "moon" in progressed_positions:
            prog_sun = progressed_positions["sun"].progressed_longitude
            prog_moon = progressed_positions["moon"].progressed_longitude
            phase_angle = (prog_moon - prog_sun) % 360
            phase_name = self._get_phase_name(phase_angle)
        else:
            phase_angle = 0
            phase_name = "Unknown"

        # Find progressed-to-natal aspects
        prog_to_natal_aspects = self._find_progressed_natal_aspects(
            progressed_positions, natal_positions, natal_houses
        )

        # Moon aspects to natal
        moon_natal_aspects = [
            a for a in prog_to_natal_aspects
            if a.body1 == "moon" or (hasattr(a, 'body1') and a.body1 == "moon")
        ]

        return ProgressedChart(
            target_date=target_date,
            age_years=age_years,
            progressed_date=progressed_date,
            jd_progressed=progressed_jd,
            positions=progressed_positions,
            progressed_mc=progressed_mc,
            progressed_asc=progressed_asc,
            natal_mc=natal_houses.mc,
            natal_asc=natal_houses.ascendant,
            moon_phase_angle=phase_angle,
            moon_phase_name=phase_name,
            moon_natal_aspects=moon_natal_aspects,
            progressed_to_natal_aspects=prog_to_natal_aspects,
        )

    def _get_phase_name(self, angle: float) -> str:
        """Get lunar phase name from Sun-Moon angle."""
        if angle < 45:
            return "New Moon"
        elif angle < 90:
            return "Crescent"
        elif angle < 135:
            return "First Quarter"
        elif angle < 180:
            return "Gibbous"
        elif angle < 225:
            return "Full Moon"
        elif angle < 270:
            return "Disseminating"
        elif angle < 315:
            return "Last Quarter"
        else:
            return "Balsamic"

    def _find_progressed_natal_aspects(
        self,
        progressed: dict[str, ProgressedPosition],
        natal_positions: dict,
        natal_houses,
    ) -> list:
        """Find aspects between progressed and natal positions."""
        aspects = []

        # Key aspect orbs for progressions (tighter than transits)
        PROG_ORBS = {
            "conjunction": 1.5,
            "opposition": 1.5,
            "trine": 1.5,
            "square": 1.5,
            "sextile": 1.0,
        }

        # Progressed bodies to check
        prog_bodies = ["sun", "moon", "mercury", "venus", "mars"]

        # Natal points to check
        natal_points = list(natal_positions.keys()) + ["ascendant", "mc"]

        for prog_body in prog_bodies:
            if prog_body not in progressed:
                continue

            prog_lon = progressed[prog_body].progressed_longitude

            for natal_point in natal_points:
                if natal_point == prog_body:
                    continue  # Skip same body

                # Get natal longitude
                if natal_point == "ascendant":
                    natal_lon = natal_houses.ascendant
                elif natal_point == "mc":
                    natal_lon = natal_houses.mc
                elif natal_point in natal_positions:
                    natal_pos = natal_positions[natal_point]
                    natal_lon = natal_pos.longitude_decimal
                else:
                    continue

                # Check each aspect
                for aspect_name, max_orb in PROG_ORBS.items():
                    aspect_angle = ASPECTS[aspect_name]["angle"]

                    # Calculate orb
                    diff = abs(prog_lon - natal_lon)
                    if diff > 180:
                        diff = 360 - diff

                    if aspect_angle == 0:
                        orb = diff
                    else:
                        orb = abs(diff - aspect_angle)

                    if orb <= max_orb:
                        aspect_result = type('AspectResult', (), {
                            'body1': f"prog_{prog_body}",
                            'body2': f"natal_{natal_point}",
                            'aspect_name': aspect_name,
                            'orb': orb,
                            'is_applying': False,  # Would need velocity calc
                            'to_dict': lambda self=None, b1=f"prog_{prog_body}",
                                              b2=f"natal_{natal_point}",
                                              an=aspect_name, o=orb: {
                                'body1': b1, 'body2': b2,
                                'aspect_name': an, 'orb': o
                            }
                        })()
                        aspects.append(aspect_result)

        return aspects

    def find_progressed_lunar_phases(
        self,
        birth_datetime: datetime,
        start_age: float = 0,
        end_age: float = 90,
        timezone: str = "UTC",
    ) -> list[ProgressedLunarPhase]:
        """
        Find all progressed New and Full Moons in a lifetime.

        The progressed lunar cycle is approximately 29.5 years.

        Args:
            birth_datetime: Birth datetime
            start_age: Starting age
            end_age: Ending age
            timezone: Birth timezone

        Returns:
            List of ProgressedLunarPhase for major phases
        """
        phases = []

        # Convert birth time
        time_result = local_to_ut(birth_datetime, timezone, 0, 0)
        natal_jd = time_result.jd_tt

        # Scan through life in 0.1 year increments
        age = start_age
        prev_phase_angle = None

        while age <= end_age:
            progressed_jd = natal_jd + age

            sun_pos = get_position("sun", progressed_jd)
            moon_pos = get_position("moon", progressed_jd)

            phase_angle = (moon_pos.longitude_decimal - sun_pos.longitude_decimal) % 360

            if prev_phase_angle is not None:
                # Check for New Moon (crossing 0°)
                if prev_phase_angle > 270 and phase_angle < 90:
                    # Refine to find exact New Moon
                    exact_age = self._refine_phase(natal_jd, age - 0.1, age, 0)
                    exact_jd = natal_jd + exact_age
                    exact_sun = get_position("sun", exact_jd)
                    exact_moon = get_position("moon", exact_jd)

                    phases.append(ProgressedLunarPhase(
                        date=birth_datetime + timedelta(days=exact_age * 365.25),
                        age_years=exact_age,
                        phase_angle=0,
                        phase_name="Progressed New Moon",
                        sun_longitude=exact_sun.longitude_decimal,
                        moon_longitude=exact_moon.longitude_decimal,
                        is_new_moon=True,
                        is_full_moon=False,
                    ))

                # Check for Full Moon (crossing 180°)
                if prev_phase_angle < 180 and phase_angle >= 180:
                    exact_age = self._refine_phase(natal_jd, age - 0.1, age, 180)
                    exact_jd = natal_jd + exact_age
                    exact_sun = get_position("sun", exact_jd)
                    exact_moon = get_position("moon", exact_jd)

                    phases.append(ProgressedLunarPhase(
                        date=birth_datetime + timedelta(days=exact_age * 365.25),
                        age_years=exact_age,
                        phase_angle=180,
                        phase_name="Progressed Full Moon",
                        sun_longitude=exact_sun.longitude_decimal,
                        moon_longitude=exact_moon.longitude_decimal,
                        is_new_moon=False,
                        is_full_moon=True,
                    ))

            prev_phase_angle = phase_angle
            age += 0.1

        return phases

    def _refine_phase(
        self,
        natal_jd: float,
        age_start: float,
        age_end: float,
        target_angle: float,
    ) -> float:
        """Refine to find exact phase angle using bisection."""
        for _ in range(20):
            age_mid = (age_start + age_end) / 2
            jd_mid = natal_jd + age_mid

            sun = get_position("sun", jd_mid)
            moon = get_position("moon", jd_mid)
            phase = (moon.longitude_decimal - sun.longitude_decimal) % 360

            # Handle wrap-around for New Moon
            if target_angle == 0:
                if phase > 180:
                    age_start = age_mid
                else:
                    age_end = age_mid
            else:
                if phase < target_angle:
                    age_start = age_mid
                else:
                    age_end = age_mid

        return (age_start + age_end) / 2


class SolarArcDirections:
    """
    Solar Arc Directions - alternative to secondary progressions.

    All planets are advanced by the same arc as the progressed Sun
    (approximately 1° per year).
    """

    def calculate_solar_arc(
        self,
        birth_datetime: datetime,
        birth_latitude: float,
        birth_longitude: float,
        target_date: datetime,
        timezone: str = "UTC",
    ) -> dict:
        """
        Calculate solar arc directed positions.

        Args:
            birth_datetime: Birth datetime
            birth_latitude: Birth latitude
            birth_longitude: Birth longitude
            target_date: Target date
            timezone: Timezone

        Returns:
            Dictionary with directed positions
        """
        # Get natal positions
        time_result = local_to_ut(
            birth_datetime, timezone, birth_latitude, birth_longitude
        )
        natal_jd = time_result.jd_tt
        natal_positions = get_all_positions(natal_jd)

        # Calculate age and progressed Sun position
        delta = target_date - birth_datetime
        age_years = delta.days / 365.25
        progressed_jd = natal_jd + age_years

        natal_sun = natal_positions["sun"].longitude_decimal
        prog_sun = get_position("sun", progressed_jd).longitude_decimal

        # Solar arc = progressed Sun - natal Sun
        solar_arc = prog_sun - natal_sun
        if solar_arc < 0:
            solar_arc += 360

        # Apply arc to all planets
        directed = {}
        for body, pos in natal_positions.items():
            directed_lon = (pos.longitude_decimal + solar_arc) % 360
            directed[body] = {
                "natal_longitude": pos.longitude_decimal,
                "directed_longitude": directed_lon,
                "solar_arc": solar_arc,
            }

        return {
            "target_date": target_date.isoformat(),
            "age_years": age_years,
            "solar_arc_degrees": solar_arc,
            "directed_positions": directed,
        }


# Module-level convenience functions
_progressions = SecondaryProgressions()
_solar_arc = SolarArcDirections()


def calculate_progressions(
    birth_datetime: datetime,
    birth_latitude: float,
    birth_longitude: float,
    target_date: datetime,
    timezone: str = "UTC",
) -> ProgressedChart:
    """Calculate progressed chart for a date."""
    return _progressions.calculate_progressed_chart(
        birth_datetime, birth_latitude, birth_longitude,
        target_date, timezone
    )


def find_progressed_lunar_phases(
    birth_datetime: datetime,
    start_age: float = 0,
    end_age: float = 90,
) -> list[ProgressedLunarPhase]:
    """Find progressed New and Full Moons."""
    return _progressions.find_progressed_lunar_phases(
        birth_datetime, start_age, end_age
    )


def calculate_solar_arc(
    birth_datetime: datetime,
    birth_latitude: float,
    birth_longitude: float,
    target_date: datetime,
    timezone: str = "UTC",
) -> dict:
    """Calculate solar arc directions."""
    return _solar_arc.calculate_solar_arc(
        birth_datetime, birth_latitude, birth_longitude,
        target_date, timezone
    )
