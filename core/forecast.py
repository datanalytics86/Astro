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

                # Get deep lunar phase meaning
                lunar_meaning = get_lunar_phase_meaning(phase_name, moon_sign)

                # Build rich description
                rich_description = f"**{description}**\n\n"
                rich_description += f"📖 {lunar_meaning.get('general', '')}\n\n"
                rich_description += f"💡 **Consejo:** {lunar_meaning.get('advice', '')}\n\n"
                rich_description += f"⚠️ **Evitar:** {lunar_meaning.get('avoid', '')}\n\n"
                rich_description += f"🔮 {lunar_meaning.get('sign_focus', '')}"

                events.append(ForecastEvent(
                    date=exact_date,
                    event_type=EventType.LUNAR_PHASE,
                    title=f"{phase_name} en {moon_sign}",
                    description=rich_description,
                    importance=importance,
                    category=category,
                    is_favorable=is_favorable,
                    details={
                        "phase": phase_name,
                        "moon_sign": moon_sign,
                        "phase_angle": phase_angle,
                        "general": lunar_meaning.get("general", ""),
                        "advice": lunar_meaning.get("advice", ""),
                        "avoid": lunar_meaning.get("avoid", ""),
                        "sign_focus": lunar_meaning.get("sign_focus", ""),
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
    """Create a personal transit event with deep interpretation."""

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

    # Get deep interpretation
    deep_meaning = get_deep_transit_meaning(transit_planet, natal_point, aspect, sign)

    # Determine favorability
    favorable_aspects = ["trine", "sextile"]
    challenging_aspects = ["square", "opposition"]
    is_favorable = aspect in favorable_aspects or (aspect == "conjunction" and transit_planet == "jupiter")

    # Build rich description
    theme = deep_meaning.get("theme", title)
    meaning = deep_meaning.get("meaning", "")
    advice = deep_meaning.get("advice", "")
    duration = deep_meaning.get("duration", "")
    sign_influence = deep_meaning.get("sign_influence", "")

    description = f"**{theme}**\n\n{meaning}\n\n💡 **Consejo:** {advice}\n\n⏱️ {duration}"
    if sign_influence:
        description += f"\n\n🔮 {sign_influence}"

    # Determine importance and category
    if transit_planet in ["pluto", "uranus"]:
        importance = 5
    elif transit_planet in ["saturn", "neptune"]:
        importance = 5 if aspect in ["conjunction", "opposition"] else 4
    else:  # jupiter
        importance = 4

    if natal_point in ["ascendant", "mc"]:
        importance = 5

    # Determine category based on natal point
    if natal_point in ["sun", "ascendant"]:
        category = DecisionCategory.NEW_BEGINNINGS
    elif natal_point == "moon":
        category = DecisionCategory.HEALTH
    elif natal_point == "venus":
        category = DecisionCategory.LOVE
    elif natal_point == "mars":
        category = DecisionCategory.CAREER
    elif natal_point == "mc":
        category = DecisionCategory.CAREER
    else:
        category = DecisionCategory.NEW_BEGINNINGS

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
            "theme": theme,
            "meaning": meaning,
            "advice": advice,
            "duration": duration,
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
# DEEP INTERPRETATIONS
# =============================================================================

TRANSIT_MEANINGS = {
    "jupiter": {
        "sun": {
            "conjunction": {
                "theme": "Año de expansión personal y éxito",
                "meaning": "Este es uno de los tránsitos más afortunados. Júpiter amplifica tu esencia, trayendo oportunidades de crecimiento, reconocimiento y abundancia. Tu confianza aumenta y las puertas se abren.",
                "advice": "Atrévete a soñar en grande. Inicia proyectos importantes, pide ese aumento, expande tu negocio. El universo te respalda.",
                "duration": "Efecto fuerte por 2-3 semanas, influencia general por 2 meses",
            },
            "trine": {
                "theme": "Flujo armónico de buena fortuna",
                "meaning": "La suerte fluye naturalmente hacia ti. Es un período donde el esfuerzo anterior da frutos sin forzar. Oportunidades llegan de forma orgánica.",
                "advice": "Mantén los ojos abiertos a oportunidades. No necesitas empujar, pero sí estar receptivo y decir que sí.",
                "duration": "Influencia positiva por 3-4 semanas",
            },
            "square": {
                "theme": "Crecimiento a través de la tensión",
                "meaning": "Puedes sentir inquietud o deseo de más. Cuidado con el exceso de confianza o gastos exagerados. El crecimiento viene, pero requiere ajustes.",
                "advice": "Modera la tendencia a exagerar. Canaliza la energía expansiva en proyectos concretos, no en fantasías.",
                "duration": "Tensión por 2-3 semanas",
            },
            "opposition": {
                "theme": "Equilibrio entre dar y recibir",
                "meaning": "Otros pueden traerte oportunidades, pero también desafíos de ego. Relaciones importantes bajo el foco. Posibles conflictos con figuras de autoridad.",
                "advice": "Escucha las perspectivas ajenas. Las oportunidades vienen de otros, no de actuar solo.",
                "duration": "Período intenso de 2-3 semanas",
            },
        },
        "moon": {
            "conjunction": {
                "theme": "Expansión emocional y bienestar",
                "meaning": "Tus emociones se expanden, sientes mayor optimismo y generosidad. Buen momento para temas domésticos, familia y bienes raíces.",
                "advice": "Confía en tu intuición. Excelente para mudanzas, comprar casa o expandir la familia.",
                "duration": "Efecto emocional por 3-4 semanas",
            },
        },
        "venus": {
            "conjunction": {
                "theme": "Bendiciones en amor y dinero",
                "meaning": "Uno de los mejores tránsitos para el amor y las finanzas. Atracción magnética, posibles encuentros significativos, mejora económica.",
                "advice": "Es momento de invertir en amor y belleza. Citas importantes, bodas, compras de lujo favorecidas.",
                "duration": "Ventana de oro por 2-3 semanas",
            },
        },
        "mars": {
            "conjunction": {
                "theme": "Energía amplificada para la acción",
                "meaning": "Tu capacidad de acción se multiplica. Entusiasmo por competir, emprender, conquistar. Cuidado con el exceso de confianza física.",
                "advice": "Canaliza esta energía en deportes, proyectos ambiciosos o causas que te apasionen.",
                "duration": "Impulso fuerte por 2-3 semanas",
            },
        },
        "ascendant": {
            "conjunction": {
                "theme": "Nuevo ciclo de 12 años comienza",
                "meaning": "Júpiter cruzando tu Ascendente marca el inicio de un nuevo ciclo vital de 12 años. Mayor visibilidad, optimismo y oportunidades personales.",
                "advice": "Reinvéntate. Nueva imagen, nuevos proyectos personales, expansión de tu horizonte vital.",
                "duration": "Influencia transformadora por 4-6 semanas",
            },
        },
        "mc": {
            "conjunction": {
                "theme": "Cúspide de éxito profesional",
                "meaning": "El punto más alto de Júpiter en tu carta. Reconocimiento público, promociones, logros profesionales visibles. Tu reputación brilla.",
                "advice": "Momento cumbre para la carrera. Pide lo que mereces, acepta posiciones de liderazgo.",
                "duration": "Período dorado profesional por 4-8 semanas",
            },
        },
    },
    "saturn": {
        "sun": {
            "conjunction": {
                "theme": "Prueba de madurez y restructuración vital",
                "meaning": "Saturno sobre tu Sol es un momento de verdad. Se revelan las estructuras de tu vida que funcionan y las que no. Puede sentirse pesado, pero construye cimientos duraderos.",
                "advice": "Acepta responsabilidades, elimina lo que no sirve. Este es el momento de construir tu legado con paciencia.",
                "duration": "Proceso profundo de 4-6 semanas, efectos por meses",
            },
            "square": {
                "theme": "Crisis de crecimiento y obstáculos",
                "meaning": "Frustraciones, retrasos y obstáculos te obligan a revisar tu dirección. No es castigo, es corrección de curso necesaria.",
                "advice": "No luches contra las limitaciones. Pregúntate qué necesita cambiar fundamentalmente.",
                "duration": "Período desafiante de 3-4 semanas",
            },
            "opposition": {
                "theme": "Confrontación con la realidad externa",
                "meaning": "Otros te reflejan tus limitaciones. Relaciones serias bajo presión. Compromisos puestos a prueba.",
                "advice": "Las relaciones que sobrevivan serán más fuertes. Deja ir las que no tienen fundamento sólido.",
                "duration": "Tensión relacional por 3-4 semanas",
            },
            "trine": {
                "theme": "Consolidación estable y logros duraderos",
                "meaning": "El trabajo duro da frutos estables. Reconocimiento por tu consistencia. Bases sólidas para el futuro.",
                "advice": "Formaliza compromisos. Excelente para estructuras legales, contratos a largo plazo.",
                "duration": "Estabilidad por 3-4 semanas",
            },
        },
        "moon": {
            "conjunction": {
                "theme": "Madurez emocional forzada",
                "meaning": "Emociones contenidas, posible melancolía o soledad. Procesamiento de temas familiares profundos. Sanación a través de la aceptación.",
                "advice": "Permite el proceso de duelo si es necesario. La madurez emocional que ganas es invaluable.",
                "duration": "Período introspectivo de 4-6 semanas",
            },
        },
        "ascendant": {
            "conjunction": {
                "theme": "Restructuración de identidad",
                "meaning": "Saturno entrando a tu primera casa inicia 2.5 años de trabajo en ti mismo. Mayor seriedad, posibles limitaciones físicas o de energía.",
                "advice": "Asume responsabilidad por tu vida. Es momento de crecer, no de quejarse.",
                "duration": "Inicio de ciclo de 2.5 años",
            },
        },
        "mc": {
            "conjunction": {
                "theme": "Cumbre de responsabilidad profesional",
                "meaning": "Saturno en tu Medio Cielo es la prueba de fuego de tu carrera. Máxima responsabilidad y visibilidad. El mundo te juzga por tus logros reales.",
                "advice": "Demuestra tu valía con hechos, no palabras. Los logros ahora definen tu legado.",
                "duration": "Período crucial de 4-8 semanas",
            },
        },
    },
    "uranus": {
        "sun": {
            "conjunction": {
                "theme": "Revolución personal y liberación",
                "meaning": "Tu vida nunca volverá a ser igual. Uranus despierta tu necesidad de autenticidad radical. Cambios inesperados que liberan tu verdadero yo.",
                "advice": "Abraza el cambio aunque asuste. Lo que se rompe necesitaba romperse. Sé auténtico.",
                "duration": "Transformación durante todo el año",
            },
            "square": {
                "theme": "Tensión entre seguridad y libertad",
                "meaning": "Inquietud extrema, deseo de romper con todo. Cuidado con decisiones impulsivas que destruyen sin construir.",
                "advice": "Haz cambios graduales, no explosiones. La libertad verdadera requiere responsabilidad.",
                "duration": "Inestabilidad por varios meses",
            },
            "opposition": {
                "theme": "Otros traen el cambio inesperado",
                "meaning": "Las sorpresas vienen de relaciones. Separaciones súbitas o encuentros revolucionarios. Tu pareja puede cambiar radicalmente.",
                "advice": "No controles a otros. Permite que las relaciones evolucionen o terminen naturalmente.",
                "duration": "Período impredecible por meses",
            },
        },
        "moon": {
            "conjunction": {
                "theme": "Revolución emocional y doméstica",
                "meaning": "Cambios súbitos en hogar, familia o vida emocional. Posible mudanza inesperada. Liberación de patrones emocionales antiguos.",
                "advice": "Tu sistema nervioso está sobreestimulado. Practica grounding. Permite el cambio emocional.",
                "duration": "Inestabilidad emocional por meses",
            },
        },
        "ascendant": {
            "conjunction": {
                "theme": "Reinvención radical de identidad",
                "meaning": "Uranus cruzando tu Ascendente te transforma de adentro hacia afuera. Nueva imagen, nueva personalidad, nueva vida.",
                "advice": "Experimenta con tu apariencia y forma de presentarte. Sé quien realmente eres.",
                "duration": "Transformación de 1-2 años",
            },
        },
    },
    "neptune": {
        "sun": {
            "conjunction": {
                "theme": "Disolución del ego y despertar espiritual",
                "meaning": "Período de confusión pero también de elevación espiritual. Tu sentido de identidad se vuelve difuso. Creatividad y compasión aumentan.",
                "advice": "No tomes decisiones importantes basadas en ilusiones. Medita, crea arte, sirve a otros.",
                "duration": "Proceso de 1-2 años",
            },
            "square": {
                "theme": "Confusión y posible engaño",
                "meaning": "Dificultad para ver la realidad claramente. Cuidado con engaños de otros o autoengaño. Escapismo tentador.",
                "advice": "Verifica todo dos veces. Evita sustancias, inversiones dudosas y personas manipuladoras.",
                "duration": "Período nebuloso por 1-2 años",
            },
        },
        "moon": {
            "conjunction": {
                "theme": "Sensibilidad psíquica aumentada",
                "meaning": "Tus emociones se vuelven porosas, absorbes el ambiente. Intuición elevada pero también vulnerabilidad emocional.",
                "advice": "Protege tu energía. Excelente para arte, espiritualidad y sanación. Evita personas tóxicas.",
                "duration": "Sensibilidad aumentada por 1-2 años",
            },
        },
    },
    "pluto": {
        "sun": {
            "conjunction": {
                "theme": "Muerte y renacimiento del ego",
                "meaning": "El tránsito más transformador. Plutón destruye lo que ya no sirve en tu identidad para que renazcas más auténtico y poderoso.",
                "advice": "Suelta el control. La transformación es inevitable. Lo que muere necesitaba morir. Emerge más fuerte.",
                "duration": "Proceso de 2-3 años",
            },
            "square": {
                "theme": "Lucha de poder y crisis",
                "meaning": "Enfrentamientos con poder externo o con tu propia sombra. Crisis que revelan dónde has dado tu poder.",
                "advice": "No entres en luchas de poder que no puedes ganar. Trabaja tu sombra interior.",
                "duration": "Intensidad por 2-3 años",
            },
            "opposition": {
                "theme": "Transformación a través de otros",
                "meaning": "Otros catalizan tu transformación. Relaciones intensas, posibles términos o renacimientos relacionales.",
                "advice": "Las relaciones superficiales mueren. Las profundas se transforman. Acepta la intensidad.",
                "duration": "Proceso relacional de 2-3 años",
            },
        },
        "moon": {
            "conjunction": {
                "theme": "Transformación emocional profunda",
                "meaning": "Plutón excava en tus emociones más profundas. Posible terapia intensa, sanación de traumas familiares, renacimiento emocional.",
                "advice": "No reprimas lo que emerge. La sanación requiere enfrentar la oscuridad. Considera terapia profunda.",
                "duration": "Proceso emocional de 2-3 años",
            },
        },
        "ascendant": {
            "conjunction": {
                "theme": "Transformación total de identidad",
                "meaning": "Plutón cruzando tu Ascendente es un renacimiento completo. La persona que eras muere para que nazca quien realmente eres.",
                "advice": "Permite la muerte simbólica. No te aferres a quien eras. Abraza tu poder personal.",
                "duration": "Transformación de 2-4 años",
            },
        },
        "mc": {
            "conjunction": {
                "theme": "Transformación de carrera y destino",
                "meaning": "Tu carrera y posición pública se transforman radicalmente. Posible ascenso al poder o caída y reconstrucción.",
                "advice": "Usa el poder con ética. Lo que construyas ahora define tu legado. Evita luchas de poder.",
                "duration": "Período de 2-4 años",
            },
        },
    },
}

LUNAR_PHASE_MEANINGS = {
    "Luna Nueva": {
        "general": "La Luna Nueva es el momento de plantar semillas. Es el inicio de un nuevo ciclo de 28 días donde tus intenciones tienen máximo poder de manifestación.",
        "advice": "Escribe tus intenciones, comienza proyectos, inicia conversaciones importantes. La energía favorece los nuevos comienzos.",
        "avoid": "No es momento de culminar o cosechar. No esperes resultados inmediatos.",
    },
    "Cuarto Creciente": {
        "general": "La Luna Creciente trae el primer desafío del ciclo. Los obstáculos que aparecen son oportunidades para fortalecer tu compromiso.",
        "advice": "Toma acción decisiva. Enfrenta los problemas directamente. Ajusta tu plan si es necesario.",
        "avoid": "No abandones ante el primer obstáculo. La persistencia es clave.",
    },
    "Luna Llena": {
        "general": "La Luna Llena ilumina lo que estaba oculto. Es momento de culminación, revelación y cosecha de lo sembrado hace dos semanas.",
        "advice": "Observa los resultados de tus acciones. Celebra logros. Libera lo que ya no sirve.",
        "avoid": "No inicies nuevos proyectos. Las emociones están intensificadas - evita decisiones impulsivas.",
    },
    "Cuarto Menguante": {
        "general": "La Luna Menguante es tiempo de soltar, reflexionar y preparar el cierre del ciclo. La energía favorece la introspección.",
        "advice": "Completa proyectos pendientes. Reflexiona sobre lo aprendido. Descansa y recarga.",
        "avoid": "No inicies nada nuevo. No es momento de empujar hacia adelante.",
    },
}

SIGN_MEANINGS_FOR_EVENTS = {
    "Aries": "energía de iniciativa, coraje y acción directa",
    "Tauro": "estabilidad, recursos materiales y placeres sensoriales",
    "Géminis": "comunicación, aprendizaje y conexiones mentales",
    "Cáncer": "hogar, familia, emociones y nutrición",
    "Leo": "creatividad, expresión personal y reconocimiento",
    "Virgo": "servicio, salud, trabajo diario y perfeccionamiento",
    "Libra": "relaciones, equilibrio, justicia y armonía",
    "Escorpio": "transformación, poder, intimidad y recursos compartidos",
    "Sagitario": "expansión, filosofía, viajes y búsqueda de significado",
    "Capricornio": "ambición, estructura, carrera y logros a largo plazo",
    "Acuario": "innovación, comunidad, libertad y visión futurista",
    "Piscis": "espiritualidad, compasión, arte y conexión universal",
}


def get_deep_transit_meaning(transit_planet: str, natal_point: str,
                             aspect: str, sign: str) -> dict:
    """Get deep interpretation for a transit."""
    planet_data = TRANSIT_MEANINGS.get(transit_planet, {})
    point_data = planet_data.get(natal_point, {})
    aspect_data = point_data.get(aspect, {})

    if aspect_data:
        result = aspect_data.copy()
        result["sign_influence"] = f"En {sign}, esto se manifiesta a través de {SIGN_MEANINGS_FOR_EVENTS.get(sign, sign)}."
        return result

    # Default interpretation if specific one not found
    return {
        "theme": f"Tránsito de {transit_planet.capitalize()} a {natal_point}",
        "meaning": f"Este tránsito activa el área de tu carta relacionada con {natal_point}.",
        "advice": "Observa los temas que emergen en esta área de tu vida.",
        "duration": "Variable según el planeta",
        "sign_influence": f"La energía se expresa a través de {SIGN_MEANINGS_FOR_EVENTS.get(sign, sign)}.",
    }


def get_lunar_phase_meaning(phase: str, moon_sign: str) -> dict:
    """Get deep interpretation for a lunar phase."""
    phase_data = LUNAR_PHASE_MEANINGS.get(phase, {})
    sign_energy = SIGN_MEANINGS_FOR_EVENTS.get(moon_sign, moon_sign)

    return {
        "general": phase_data.get("general", ""),
        "advice": phase_data.get("advice", ""),
        "avoid": phase_data.get("avoid", ""),
        "sign_focus": f"Con la Luna en {moon_sign}, el foco está en {sign_energy}. Los temas de {moon_sign} están especialmente activados.",
    }


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
