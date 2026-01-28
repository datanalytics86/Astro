#!/usr/bin/env python3
"""
Advanced Astrological Forecasting Module

Calculates personalized astronomical milestones and optimal decision dates.
This is advanced astrological engineering for life planning.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum

import swisseph as swe

from .time_engine import datetime_to_jd, jd_to_datetime
from .ephemeris import get_position, get_all_positions, PLANETS


class EventType(Enum):
    """Types of astrological events."""
    LUNAR_PHASE = "lunar_phase"
    TRANSIT = "transit"
    RETROGRADE = "retrograde"
    INGRESS = "ingress"
    ECLIPSE = "eclipse"
    POWER_DAY = "power_day"
    DECISION_WINDOW = "decision_window"


class DecisionCategory(Enum):
    """Categories for decision making."""
    FINANCES = "finances"
    LOVE = "love"
    CAREER = "career"
    HEALTH = "health"
    TRAVEL = "travel"
    CONTRACTS = "contracts"
    NEW_BEGINNINGS = "new_beginnings"
    COMPLETION = "completion"


@dataclass
class ForecastEvent:
    """A forecasted astrological event."""
    date: datetime
    event_type: EventType
    title: str
    description: str
    importance: int  # 1-5, 5 being most important
    category: Optional[DecisionCategory] = None
    is_favorable: bool = True
    details: Dict = field(default_factory=dict)


@dataclass
class PersonalForecast:
    """Complete personal forecast for a period."""
    natal_sun_sign: str
    natal_moon_sign: str
    natal_rising_sign: str
    start_date: datetime
    end_date: datetime
    events: List[ForecastEvent] = field(default_factory=list)
    power_days: List[datetime] = field(default_factory=list)
    challenging_days: List[datetime] = field(default_factory=list)


# =============================================================================
# LUNAR PHASES
# =============================================================================

def find_lunar_phases(start_date: datetime, end_date: datetime) -> List[ForecastEvent]:
    """Find all lunar phases (New Moon, Full Moon, quarters) in date range."""
    events = []

    current = start_date
    jd = datetime_to_jd(current)

    while current < end_date:
        # Get Sun and Moon positions
        sun_pos = get_position("sun", jd)
        moon_pos = get_position("moon", jd)

        # Calculate lunar phase angle
        phase_angle = (moon_pos.longitude_decimal - sun_pos.longitude_decimal) % 360

        # Check for phase (with 1 degree tolerance)
        phase_name = None
        importance = 3
        is_favorable = True

        if phase_angle < 2 or phase_angle > 358:
            phase_name = "Luna Nueva"
            importance = 5
            description = "Momento ideal para nuevos comienzos, sembrar intenciones y proyectos."
            category = DecisionCategory.NEW_BEGINNINGS
        elif 88 < phase_angle < 92:
            phase_name = "Cuarto Creciente"
            importance = 3
            description = "Momento de acción y superar obstáculos. Toma decisiones con determinación."
            category = DecisionCategory.CAREER
        elif 178 < phase_angle < 182:
            phase_name = "Luna Llena"
            importance = 5
            description = "Culminación y revelaciones. Evita decisiones impulsivas, observa resultados."
            category = DecisionCategory.COMPLETION
            is_favorable = False  # Not ideal for new starts
        elif 268 < phase_angle < 272:
            phase_name = "Cuarto Menguante"
            importance = 3
            description = "Momento de soltar, reflexionar y preparar el cierre de ciclos."
            category = DecisionCategory.COMPLETION

        if phase_name:
            # Refine exact time using bisection
            exact_jd = refine_lunar_phase(jd - 1, jd + 1, phase_angle)
            exact_date = jd_to_datetime(exact_jd)

            if start_date <= exact_date <= end_date:
                moon_sign = get_zodiac_sign(moon_pos.longitude_decimal)

                events.append(ForecastEvent(
                    date=exact_date,
                    event_type=EventType.LUNAR_PHASE,
                    title=f"{phase_name} en {moon_sign}",
                    description=description,
                    importance=importance,
                    category=category,
                    is_favorable=is_favorable,
                    details={
                        "phase": phase_name,
                        "moon_sign": moon_sign,
                        "phase_angle": phase_angle,
                    }
                ))

        # Move forward
        jd += 1
        current = jd_to_datetime(jd)

    return events


def refine_lunar_phase(jd_start: float, jd_end: float, target_angle: float) -> float:
    """Refine lunar phase time using bisection."""
    tolerance = 0.001  # About 1.4 minutes

    for _ in range(50):
        jd_mid = (jd_start + jd_end) / 2
        sun_pos = get_position("sun", jd_mid)
        moon_pos = get_position("moon", jd_mid)
        phase = (moon_pos.longitude_decimal - sun_pos.longitude_decimal) % 360

        # Normalize target for comparison
        if target_angle > 350:
            target = 0
        else:
            target = target_angle

        if abs(phase - target) < 0.5 or (jd_end - jd_start) < tolerance:
            return jd_mid

        if phase < target or (target < 10 and phase > 350):
            jd_start = jd_mid
        else:
            jd_end = jd_mid

    return (jd_start + jd_end) / 2


# =============================================================================
# RETROGRADE PERIODS
# =============================================================================

def find_retrograde_periods(start_date: datetime, end_date: datetime) -> List[ForecastEvent]:
    """Find all retrograde stations and periods."""
    events = []

    # Focus on personal planets that affect daily life
    retrograde_planets = ["mercury", "venus", "mars"]

    jd_start = datetime_to_jd(start_date)
    jd_end = datetime_to_jd(end_date)

    for planet in retrograde_planets:
        # Scan for retrograde stations
        jd = jd_start
        prev_speed = None

        while jd < jd_end:
            pos = get_position(planet, jd)

            if prev_speed is not None:
                # Detect station (speed crosses zero)
                if prev_speed > 0 and pos.speed_longitude < 0:
                    # Station retrograde
                    exact_jd = refine_station(jd - 1, jd, planet)
                    exact_date = jd_to_datetime(exact_jd)
                    sign = get_zodiac_sign(pos.longitude_decimal)

                    events.append(create_retrograde_event(
                        planet, exact_date, sign, "retrograde"
                    ))

                elif prev_speed < 0 and pos.speed_longitude > 0:
                    # Station direct
                    exact_jd = refine_station(jd - 1, jd, planet)
                    exact_date = jd_to_datetime(exact_jd)
                    sign = get_zodiac_sign(pos.longitude_decimal)

                    events.append(create_retrograde_event(
                        planet, exact_date, sign, "direct"
                    ))

            prev_speed = pos.speed_longitude
            jd += 1

    return events


def refine_station(jd_start: float, jd_end: float, planet: str) -> float:
    """Refine station time using bisection."""
    tolerance = 0.001

    for _ in range(50):
        jd_mid = (jd_start + jd_end) / 2
        pos = get_position(planet, jd_mid)

        if abs(pos.speed_longitude) < 0.001 or (jd_end - jd_start) < tolerance:
            return jd_mid

        pos_start = get_position(planet, jd_start)
        if (pos_start.speed_longitude > 0) == (pos.speed_longitude > 0):
            jd_start = jd_mid
        else:
            jd_end = jd_mid

    return (jd_start + jd_end) / 2


def create_retrograde_event(planet: str, date: datetime, sign: str,
                            station_type: str) -> ForecastEvent:
    """Create a retrograde event with interpretations."""

    planet_names = {
        "mercury": "Mercurio",
        "venus": "Venus",
        "mars": "Marte",
    }

    planet_name = planet_names.get(planet, planet.capitalize())

    if station_type == "retrograde":
        title = f"{planet_name} Retrógrado en {sign}"
        is_favorable = False

        if planet == "mercury":
            description = (
                "Evita firmar contratos, hacer compras tecnológicas importantes o "
                "iniciar nuevos proyectos de comunicación. Ideal para revisar, "
                "reconectar y reflexionar."
            )
            category = DecisionCategory.CONTRACTS
            importance = 4
        elif planet == "venus":
            description = (
                "No es momento ideal para bodas, cirugías estéticas o grandes "
                "compras de lujo. Excelente para reconectar con ex-parejas o "
                "revisar valores personales."
            )
            category = DecisionCategory.LOVE
            importance = 4
        else:  # mars
            description = (
                "Evita confrontaciones directas, cirugías electivas o iniciar "
                "batallas legales. La energía está mejor dirigida hacia proyectos "
                "ya iniciados."
            )
            category = DecisionCategory.CAREER
            importance = 4
    else:  # direct
        title = f"{planet_name} Directo en {sign}"
        is_favorable = True
        importance = 3

        if planet == "mercury":
            description = (
                "¡Luz verde para comunicaciones! Buen momento para firmar, "
                "comprar tecnología y lanzar proyectos."
            )
            category = DecisionCategory.CONTRACTS
        elif planet == "venus":
            description = (
                "El amor y las finanzas fluyen mejor. Buen momento para "
                "decisiones románticas y compras importantes."
            )
            category = DecisionCategory.LOVE
        else:  # mars
            description = (
                "La energía de acción se desbloquea. Adelante con nuevas "
                "iniciativas y proyectos que requieren determinación."
            )
            category = DecisionCategory.CAREER

    return ForecastEvent(
        date=date,
        event_type=EventType.RETROGRADE,
        title=title,
        description=description,
        importance=importance,
        category=category,
        is_favorable=is_favorable,
        details={
            "planet": planet,
            "sign": sign,
            "station_type": station_type,
        }
    )


# =============================================================================
# PERSONAL TRANSITS TO NATAL CHART
# =============================================================================

def find_personal_transits(natal_positions: Dict[str, float],
                           start_date: datetime,
                           end_date: datetime) -> List[ForecastEvent]:
    """Find significant transits to natal chart."""
    events = []

    # Outer planets that create significant life events
    transiting_planets = ["jupiter", "saturn", "uranus", "neptune", "pluto"]

    # Key natal points
    natal_points = ["sun", "moon", "mercury", "venus", "mars", "ascendant", "mc"]

    # Major aspects to track
    aspects = {
        "conjunction": (0, 2),
        "opposition": (180, 2),
        "trine": (120, 2),
        "square": (90, 2),
        "sextile": (60, 1.5),
    }

    jd_start = datetime_to_jd(start_date)
    jd_end = datetime_to_jd(end_date)

    for transit_planet in transiting_planets:
        for natal_point, natal_lon in natal_positions.items():
            if natal_point not in natal_points:
                continue

            # Scan for aspects
            jd = jd_start
            while jd < jd_end:
                transit_pos = get_position(transit_planet, jd)

                for aspect_name, (angle, orb) in aspects.items():
                    diff = abs((transit_pos.longitude_decimal - natal_lon + 180) % 360 - 180)
                    aspect_diff = abs(diff - angle) if angle != 0 else diff

                    if aspect_diff < 0.5:  # Very tight orb for exact date
                        exact_date = jd_to_datetime(jd)

                        event = create_transit_event(
                            transit_planet, natal_point, aspect_name,
                            exact_date, transit_pos.longitude_decimal
                        )

                        # Avoid duplicates (check if similar event exists within 5 days)
                        is_duplicate = any(
                            abs((e.date - exact_date).days) < 5 and
                            e.details.get("transit_planet") == transit_planet and
                            e.details.get("natal_point") == natal_point
                            for e in events
                        )

                        if not is_duplicate:
                            events.append(event)

                jd += 1

    return events


def create_transit_event(transit_planet: str, natal_point: str,
                         aspect: str, date: datetime,
                         transit_longitude: float) -> ForecastEvent:
    """Create a personal transit event."""

    planet_names = {
        "jupiter": "Júpiter",
        "saturn": "Saturno",
        "uranus": "Urano",
        "neptune": "Neptuno",
        "pluto": "Plutón",
    }

    natal_names = {
        "sun": "Sol natal",
        "moon": "Luna natal",
        "mercury": "Mercurio natal",
        "venus": "Venus natal",
        "mars": "Marte natal",
        "ascendant": "Ascendente",
        "mc": "Medio Cielo",
    }

    aspect_names = {
        "conjunction": "conjunción",
        "opposition": "oposición",
        "trine": "trígono",
        "square": "cuadratura",
        "sextile": "sextil",
    }

    t_name = planet_names.get(transit_planet, transit_planet.capitalize())
    n_name = natal_names.get(natal_point, natal_point.capitalize())
    a_name = aspect_names.get(aspect, aspect)
    sign = get_zodiac_sign(transit_longitude)

    title = f"{t_name} {a_name} {n_name}"

    # Determine favorability and interpretation
    favorable_aspects = ["trine", "sextile", "conjunction"]
    is_favorable = aspect in favorable_aspects

    if transit_planet == "jupiter":
        importance = 4
        if aspect in favorable_aspects:
            description = f"Expansión y oportunidades en el área de tu {n_name}. Momento favorable para crecer."
            category = DecisionCategory.NEW_BEGINNINGS
        else:
            description = f"Tensión de crecimiento. Cuidado con excesos relacionados con tu {n_name}."
            category = DecisionCategory.CAREER

    elif transit_planet == "saturn":
        importance = 5
        if aspect == "conjunction":
            description = f"Momento de madurez y responsabilidad. Estructuración importante de tu {n_name}."
            is_favorable = True  # Challenging but constructive
        elif aspect in ["trine", "sextile"]:
            description = f"Estabilidad y consolidación. Buen momento para compromisos a largo plazo."
        else:
            description = f"Pruebas y restricciones. Período de aprendizaje kármico importante."
            is_favorable = False
        category = DecisionCategory.CAREER

    elif transit_planet == "uranus":
        importance = 5
        description = f"Cambios inesperados y liberación. Revolución en el área de tu {n_name}."
        category = DecisionCategory.NEW_BEGINNINGS
        is_favorable = aspect in favorable_aspects

    elif transit_planet == "neptune":
        importance = 4
        if aspect in favorable_aspects:
            description = f"Inspiración espiritual y creatividad elevada en tu {n_name}."
        else:
            description = f"Confusión o desilusión posible. Evita decisiones importantes sin claridad."
            is_favorable = False
        category = DecisionCategory.HEALTH

    else:  # pluto
        importance = 5
        description = f"Transformación profunda y renacimiento en el área de tu {n_name}."
        category = DecisionCategory.COMPLETION

    return ForecastEvent(
        date=date,
        event_type=EventType.TRANSIT,
        title=title,
        description=description,
        importance=importance,
        category=category,
        is_favorable=is_favorable,
        details={
            "transit_planet": transit_planet,
            "natal_point": natal_point,
            "aspect": aspect,
            "sign": sign,
        }
    )


# =============================================================================
# PLANETARY INGRESSES
# =============================================================================

def find_ingresses(start_date: datetime, end_date: datetime) -> List[ForecastEvent]:
    """Find planetary sign changes (ingresses)."""
    events = []

    planets = ["sun", "mercury", "venus", "mars", "jupiter", "saturn"]

    jd_start = datetime_to_jd(start_date)
    jd_end = datetime_to_jd(end_date)

    for planet in planets:
        jd = jd_start
        prev_sign = None

        while jd < jd_end:
            pos = get_position(planet, jd)
            current_sign = get_zodiac_sign(pos.longitude_decimal)

            if prev_sign is not None and current_sign != prev_sign:
                exact_date = jd_to_datetime(jd)

                events.append(create_ingress_event(planet, current_sign, exact_date))

            prev_sign = current_sign
            jd += 1

    return events


def create_ingress_event(planet: str, sign: str, date: datetime) -> ForecastEvent:
    """Create an ingress event."""

    planet_names = {
        "sun": "Sol",
        "mercury": "Mercurio",
        "venus": "Venus",
        "mars": "Marte",
        "jupiter": "Júpiter",
        "saturn": "Saturno",
    }

    p_name = planet_names.get(planet, planet.capitalize())
    title = f"{p_name} entra en {sign}"

    # Sign element for interpretation
    fire_signs = ["Aries", "Leo", "Sagitario"]
    earth_signs = ["Tauro", "Virgo", "Capricornio"]
    air_signs = ["Géminis", "Libra", "Acuario"]
    water_signs = ["Cáncer", "Escorpio", "Piscis"]

    if sign in fire_signs:
        element = "fuego"
        quality = "energía activa, iniciativa y entusiasmo"
    elif sign in earth_signs:
        element = "tierra"
        quality = "practicidad, estabilidad y resultados concretos"
    elif sign in air_signs:
        element = "aire"
        quality = "comunicación, ideas y conexiones sociales"
    else:
        element = "agua"
        quality = "emociones, intuición y profundidad"

    if planet == "sun":
        importance = 3
        description = f"Nueva temporada astrológica. Énfasis colectivo en {quality}."
    elif planet in ["jupiter", "saturn"]:
        importance = 5
        description = f"Cambio importante de ciclo. Los próximos meses favorecen {quality}."
    else:
        importance = 2
        description = f"Cambio de energía hacia {quality}."

    return ForecastEvent(
        date=date,
        event_type=EventType.INGRESS,
        title=title,
        description=description,
        importance=importance,
        is_favorable=True,
        details={
            "planet": planet,
            "sign": sign,
            "element": element,
        }
    )


# =============================================================================
# DECISION WINDOWS
# =============================================================================

def calculate_decision_windows(events: List[ForecastEvent],
                               start_date: datetime,
                               end_date: datetime) -> List[ForecastEvent]:
    """Calculate optimal windows for different types of decisions."""
    decision_events = []

    # Find Mercury retrograde periods
    mercury_retro_periods = []
    current_retro_start = None

    for event in sorted(events, key=lambda e: e.date):
        if event.details.get("planet") == "mercury":
            if event.details.get("station_type") == "retrograde":
                current_retro_start = event.date
            elif event.details.get("station_type") == "direct" and current_retro_start:
                mercury_retro_periods.append((current_retro_start, event.date))
                current_retro_start = None

    # Find favorable windows
    current = start_date
    while current < end_date:
        jd = datetime_to_jd(current)

        # Check if in Mercury retrograde
        in_mercury_retro = any(
            start <= current <= end for start, end in mercury_retro_periods
        )

        # Get moon position for VOC check (simplified)
        moon_pos = get_position("moon", jd)
        moon_sign = get_zodiac_sign(moon_pos.longitude_decimal)

        # Get other planetary positions
        venus_pos = get_position("venus", jd)
        mars_pos = get_position("mars", jd)
        jupiter_pos = get_position("jupiter", jd)

        # Check for favorable aspects
        sun_pos = get_position("sun", jd)

        # Venus-Jupiter positive aspect (good for love/money)
        venus_jupiter_diff = abs((venus_pos.longitude_decimal - jupiter_pos.longitude_decimal + 180) % 360 - 180)
        if venus_jupiter_diff < 3 or abs(venus_jupiter_diff - 120) < 3 or abs(venus_jupiter_diff - 60) < 3:
            decision_events.append(ForecastEvent(
                date=current,
                event_type=EventType.DECISION_WINDOW,
                title="Ventana favorable para amor y finanzas",
                description="Venus y Júpiter en armonía. Excelente para decisiones románticas, inversiones y compras importantes.",
                importance=4,
                category=DecisionCategory.FINANCES,
                is_favorable=True,
                details={"type": "venus_jupiter"}
            ))

        # Mars-Jupiter positive aspect (good for action/career)
        mars_jupiter_diff = abs((mars_pos.longitude_decimal - jupiter_pos.longitude_decimal + 180) % 360 - 180)
        if mars_jupiter_diff < 3 or abs(mars_jupiter_diff - 120) < 3:
            decision_events.append(ForecastEvent(
                date=current,
                event_type=EventType.DECISION_WINDOW,
                title="Ventana de acción exitosa",
                description="Marte y Júpiter en armonía. Ideal para lanzar proyectos, competencias y acciones audaces.",
                importance=4,
                category=DecisionCategory.CAREER,
                is_favorable=True,
                details={"type": "mars_jupiter"}
            ))

        current += timedelta(days=1)

    return decision_events


# =============================================================================
# POWER DAYS
# =============================================================================

def calculate_power_days(natal_sun_longitude: float,
                         natal_moon_longitude: float,
                         start_date: datetime,
                         end_date: datetime) -> List[ForecastEvent]:
    """Calculate personal power days based on natal chart."""
    events = []

    current = start_date
    while current < end_date:
        jd = datetime_to_jd(current)

        # Get transiting positions
        sun_pos = get_position("sun", jd)
        moon_pos = get_position("moon", jd)

        power_score = 0
        reasons = []

        # Sun return to natal Sun (birthday power)
        sun_diff = abs(sun_pos.longitude_decimal - natal_sun_longitude)
        if sun_diff < 1 or sun_diff > 359:
            power_score += 5
            reasons.append("Sol en posición natal (cumpleaños solar)")

        # Moon return to natal Moon
        moon_diff = abs(moon_pos.longitude_decimal - natal_moon_longitude)
        if moon_diff < 2 or moon_diff > 358:
            power_score += 3
            reasons.append("Luna en posición natal")

        # Sun trine natal Sun
        if abs(sun_diff - 120) < 2 or abs(sun_diff - 240) < 2:
            power_score += 2
            reasons.append("Sol en trígono a posición natal")

        # Moon conjunct natal Sun
        moon_sun_diff = abs(moon_pos.longitude_decimal - natal_sun_longitude)
        if moon_sun_diff < 2 or moon_sun_diff > 358:
            power_score += 2
            reasons.append("Luna sobre Sol natal")

        # Jupiter aspects to natal Sun
        jupiter_pos = get_position("jupiter", jd)
        jup_sun_diff = abs((jupiter_pos.longitude_decimal - natal_sun_longitude + 180) % 360 - 180)
        if jup_sun_diff < 2:
            power_score += 4
            reasons.append("Júpiter conjunción Sol natal")
        elif abs(jup_sun_diff - 120) < 2:
            power_score += 3
            reasons.append("Júpiter trígono Sol natal")

        if power_score >= 3:
            events.append(ForecastEvent(
                date=current,
                event_type=EventType.POWER_DAY,
                title=f"Día de Poder Personal ({power_score}/10)",
                description=f"Factores: {', '.join(reasons)}. Excelente para decisiones importantes.",
                importance=min(5, power_score),
                category=DecisionCategory.NEW_BEGINNINGS,
                is_favorable=True,
                details={
                    "power_score": power_score,
                    "reasons": reasons,
                }
            ))

        current += timedelta(days=1)

    return events


# =============================================================================
# MAIN FORECAST FUNCTION
# =============================================================================

def generate_personal_forecast(birth_datetime: datetime,
                               latitude: float,
                               longitude: float,
                               timezone: str,
                               forecast_months: int = 12) -> PersonalForecast:
    """Generate complete personal forecast."""
    from .time_engine import local_to_ut
    from .houses import calculate_houses

    # Calculate natal chart
    time_result = local_to_ut(birth_datetime, timezone, latitude, longitude)
    natal_positions = get_all_positions(time_result.jd_tt)
    houses = calculate_houses(time_result.jd_ut, latitude, longitude, "P")

    # Extract key positions
    natal_sun = natal_positions["sun"].longitude_decimal
    natal_moon = natal_positions["moon"].longitude_decimal

    natal_dict = {body: pos.longitude_decimal for body, pos in natal_positions.items()}
    natal_dict["ascendant"] = houses.ascendant
    natal_dict["mc"] = houses.mc

    # Date range
    start_date = datetime.now()
    end_date = start_date + timedelta(days=forecast_months * 30)

    # Gather all events
    all_events = []

    # Lunar phases
    all_events.extend(find_lunar_phases(start_date, end_date))

    # Retrograde periods
    all_events.extend(find_retrograde_periods(start_date, end_date))

    # Personal transits
    all_events.extend(find_personal_transits(natal_dict, start_date, end_date))

    # Ingresses
    all_events.extend(find_ingresses(start_date, end_date))

    # Decision windows
    all_events.extend(calculate_decision_windows(all_events, start_date, end_date))

    # Power days
    all_events.extend(calculate_power_days(natal_sun, natal_moon, start_date, end_date))

    # Sort by date
    all_events.sort(key=lambda e: e.date)

    # Identify power and challenging days
    power_days = [e.date for e in all_events
                  if e.event_type == EventType.POWER_DAY and e.importance >= 4]

    challenging_days = [e.date for e in all_events
                        if not e.is_favorable and e.importance >= 4]

    return PersonalForecast(
        natal_sun_sign=get_zodiac_sign(natal_sun),
        natal_moon_sign=get_zodiac_sign(natal_moon),
        natal_rising_sign=get_zodiac_sign(houses.ascendant),
        start_date=start_date,
        end_date=end_date,
        events=all_events,
        power_days=power_days,
        challenging_days=challenging_days,
    )


# =============================================================================
# HELPERS
# =============================================================================

def get_zodiac_sign(longitude: float) -> str:
    """Get zodiac sign from longitude."""
    signs = [
        "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
        "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
    ]
    return signs[int(longitude / 30) % 12]


def filter_events_by_category(events: List[ForecastEvent],
                              category: DecisionCategory) -> List[ForecastEvent]:
    """Filter events by decision category."""
    return [e for e in events if e.category == category]


def filter_events_by_importance(events: List[ForecastEvent],
                                min_importance: int = 3) -> List[ForecastEvent]:
    """Filter events by minimum importance."""
    return [e for e in events if e.importance >= min_importance]


def get_monthly_summary(events: List[ForecastEvent],
                        month: int, year: int) -> Dict:
    """Get summary of events for a specific month."""
    month_events = [
        e for e in events
        if e.date.month == month and e.date.year == year
    ]

    return {
        "total_events": len(month_events),
        "favorable": len([e for e in month_events if e.is_favorable]),
        "challenging": len([e for e in month_events if not e.is_favorable]),
        "power_days": len([e for e in month_events if e.event_type == EventType.POWER_DAY]),
        "high_importance": len([e for e in month_events if e.importance >= 4]),
        "events": month_events,
    }
