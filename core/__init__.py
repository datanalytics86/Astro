"""
Core module for astrological engineering calculations.

This package provides high-precision astronomical calculations for
astrological analysis, including:

- Time conversions (time_engine)
- Planetary positions (ephemeris)
- House systems (houses)
- Aspect detection (aspects)
- Transit finding (transits)
- Station detection (stations)
- Sign ingress detection (ingress)
- Activation windows (windows)
- Solar returns (solar_returns)
- Secondary progressions (progressions)
- Validation against JPL Horizons (validation)
"""

from .time_engine import (
    TimeEngine,
    TimeResult,
    local_to_ut,
    datetime_to_jd,
    jd_to_datetime,
    get_delta_t,
    get_timezone_for_location,
)

from .ephemeris import (
    EphemerisEngine,
    PlanetPosition,
    get_position,
    get_all_positions,
    get_lunar_phase,
    set_ephemeris_path,
    BODY_MAP,
)

from .houses import (
    HouseCalculator,
    HouseData,
    calculate_houses,
    compare_house_systems,
    HOUSE_SYSTEMS,
)

from .aspects import (
    AspectEngine,
    AspectResult,
    find_aspect,
    find_all_aspects,
    aspect_matrix,
    calculate_aspect_summary,
    ASPECTS,
)

from .transits import (
    TransitFinder,
    TransitEvent,
    TransitTimeline,
    find_transit,
    find_all_transits,
)

from .stations import (
    StationFinder,
    StationEvent,
    find_stations,
    find_all_stations,
    get_retrograde_periods,
)

from .ingress import (
    IngressFinder,
    IngressEvent,
    find_ingresses,
    find_all_ingresses,
)

from .windows import (
    ActivationEngine,
    ActivationWindow,
    calculate_activation,
    find_peak_windows,
)

from .solar_returns import (
    SolarReturnCalculator,
    SolarReturnData,
    calculate_solar_return,
    find_solar_return_time,
)

from .progressions import (
    SecondaryProgressions,
    ProgressedChart,
    ProgressedLunarPhase,
    calculate_progressions,
    find_progressed_lunar_phases,
    calculate_solar_arc,
)

from .validation import (
    JPLHorizonsValidator,
    ValidationResult,
    validate_against_jpl,
    validate_all,
    run_internal_checks,
)

__all__ = [
    # Time
    "TimeEngine",
    "TimeResult",
    "local_to_ut",
    "datetime_to_jd",
    "jd_to_datetime",
    "get_delta_t",
    "get_timezone_for_location",
    # Ephemeris
    "EphemerisEngine",
    "PlanetPosition",
    "get_position",
    "get_all_positions",
    "get_lunar_phase",
    "set_ephemeris_path",
    "BODY_MAP",
    # Houses
    "HouseCalculator",
    "HouseData",
    "calculate_houses",
    "compare_house_systems",
    "HOUSE_SYSTEMS",
    # Aspects
    "AspectEngine",
    "AspectResult",
    "find_aspect",
    "find_all_aspects",
    "aspect_matrix",
    "calculate_aspect_summary",
    "ASPECTS",
    # Transits
    "TransitFinder",
    "TransitEvent",
    "TransitTimeline",
    "find_transit",
    "find_all_transits",
    # Stations
    "StationFinder",
    "StationEvent",
    "find_stations",
    "find_all_stations",
    "get_retrograde_periods",
    # Ingress
    "IngressFinder",
    "IngressEvent",
    "find_ingresses",
    "find_all_ingresses",
    # Windows
    "ActivationEngine",
    "ActivationWindow",
    "calculate_activation",
    "find_peak_windows",
    # Solar Returns
    "SolarReturnCalculator",
    "SolarReturnData",
    "calculate_solar_return",
    "find_solar_return_time",
    # Progressions
    "SecondaryProgressions",
    "ProgressedChart",
    "ProgressedLunarPhase",
    "calculate_progressions",
    "find_progressed_lunar_phases",
    "calculate_solar_arc",
    # Validation
    "JPLHorizonsValidator",
    "ValidationResult",
    "validate_against_jpl",
    "validate_all",
    "run_internal_checks",
]
