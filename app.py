#!/usr/bin/env python3
"""
Astro Engineering - Streamlit Web Application

Interactive web interface for astrological calculations.
Run with: streamlit run app.py
"""

import sys
from pathlib import Path
from datetime import datetime, date, time
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.time_engine import local_to_ut, TimeEngine
from core.ephemeris import get_all_positions, EphemerisEngine
from core.houses import calculate_houses, compare_house_systems, HOUSE_SYSTEMS
from core.aspects import find_all_aspects, aspect_matrix, calculate_aspect_summary
from core.transits import find_all_transits
from core.stations import find_all_stations
from core.ingress import find_all_ingresses
from core.solar_returns import calculate_solar_return
from core.progressions import calculate_progressions, find_progressed_lunar_phases
from core.interpretations import (
    get_translation,
    get_planet_interpretation,
    TRANSIT_INTERPRETATIONS,
    PLANET_IN_SIGN,
)
from data.symbols import (
    longitude_to_zodiacal,
    ZODIAC_SYMBOLS,
    PLANET_SYMBOLS,
    ZODIAC_SIGNS,
)

# Page configuration
st.set_page_config(
    page_title="Astro Engineering",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize language in session state
if "lang" not in st.session_state:
    st.session_state.lang = "es"

# Translation helper
def t(key):
    return get_translation(key, st.session_state.lang)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stDataFrame {
        font-size: 0.9rem;
    }
    .interpretation-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #6366f1;
    }
    .forecast-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 3px solid #10b981;
    }
</style>
""", unsafe_allow_html=True)


def get_sign_from_longitude(longitude_deg):
    """Get zodiac sign from longitude in degrees."""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_index = int(longitude_deg / 30) % 12
    return signs[sign_index]


def get_planet_symbol(planet):
    """Get planet symbol."""
    symbols = {
        "sun": "☉", "moon": "☽", "mercury": "☿", "venus": "♀", "mars": "♂",
        "jupiter": "♃", "saturn": "♄", "uranus": "♅", "neptune": "♆", "pluto": "♇",
    }
    return symbols.get(planet, "")


def main():
    """Main application entry point."""
    lang = st.session_state.lang

    # Sidebar navigation
    st.sidebar.title("🔭 Astro Engineering")

    # Language selector
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('language')}")
    lang_options = {"Español": "es", "English": "en"}
    selected_lang = st.sidebar.radio(
        "Idioma / Language",
        options=list(lang_options.keys()),
        index=0 if lang == "es" else 1,
        label_visibility="collapsed"
    )
    if lang_options[selected_lang] != lang:
        st.session_state.lang = lang_options[selected_lang]
        st.rerun()

    st.sidebar.markdown("---")

    # Navigation labels based on language
    if lang == "es":
        nav_labels = [
            "🏠 Inicio",
            "📊 Carta Natal",
            "🔄 Tránsitos",
            "🌙 Retorno Solar",
            "📈 Progresiones",
            "🪐 Efemérides",
            "⚙️ Configuración",
        ]
    else:
        nav_labels = [
            "🏠 Home",
            "📊 Natal Chart",
            "🔄 Transits",
            "🌙 Solar Return",
            "📈 Progressions",
            "🪐 Ephemeris",
            "⚙️ Settings",
        ]

    page = st.sidebar.radio(
        "Navigation" if lang == "en" else "Navegación",
        nav_labels,
    )

    # Route to appropriate page
    if "Inicio" in page or "Home" in page:
        show_home()
    elif "Carta Natal" in page or "Natal Chart" in page:
        show_natal_chart()
    elif "Tránsitos" in page or "Transits" in page:
        show_transits()
    elif "Retorno Solar" in page or "Solar Return" in page:
        show_solar_return()
    elif "Progresiones" in page or "Progressions" in page:
        show_progressions()
    elif "Efemérides" in page or "Ephemeris" in page:
        show_ephemeris()
    elif "Configuración" in page or "Settings" in page:
        show_settings()


def show_home():
    """Home page with overview."""
    lang = st.session_state.lang

    st.markdown('<p class="main-header">Astro Engineering</p>', unsafe_allow_html=True)

    if lang == "es":
        st.markdown(
            '<p class="sub-header">Cálculos Astronómicos de Alta Precisión para Análisis Astrológico</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p class="sub-header">High-Precision Astronomical Calculations for Astrological Analysis</p>',
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        if lang == "es":
            st.markdown("### 🎯 Precisión")
            st.markdown("""
            - Cálculos con Swiss Ephemeris
            - Precisión ~0.001 segundos de arco
            - Múltiples sistemas de casas
            - Validado contra JPL Horizons
            """)
        else:
            st.markdown("### 🎯 Precision")
            st.markdown("""
            - Swiss Ephemeris calculations
            - ~0.001 arcsecond accuracy
            - Multiple house systems
            - Validated against JPL Horizons
            """)

    with col2:
        if lang == "es":
            st.markdown("### 📊 Funciones")
            st.markdown("""
            - Cálculo de carta natal
            - Análisis de tránsitos
            - Retornos solares
            - Progresiones secundarias
            - **Interpretaciones astrológicas**
            """)
        else:
            st.markdown("### 📊 Features")
            st.markdown("""
            - Natal chart calculation
            - Transit analysis
            - Solar returns
            - Secondary progressions
            - **Astrological interpretations**
            """)

    with col3:
        if lang == "es":
            st.markdown("### 🔧 Técnico")
            st.markdown("""
            - Conversiones de escalas de tiempo
            - Cálculos de Delta-T
            - Detección de retrogradación
            - Exportar a JSON/iCal
            """)
        else:
            st.markdown("### 🔧 Technical")
            st.markdown("""
            - Time scale conversions
            - Delta-T calculations
            - Retrograde detection
            - Export to JSON/iCal
            """)

    st.markdown("---")

    # Quick calculator
    if lang == "es":
        st.subheader("Calculadora Rápida de Posiciones")
    else:
        st.subheader("Quick Position Calculator")

    col1, col2 = st.columns(2)

    with col1:
        calc_date = st.date_input(
            "Fecha" if lang == "es" else "Date",
            value=date.today()
        )
        calc_time = st.time_input(
            "Hora (UTC)" if lang == "es" else "Time (UTC)",
            value=time(12, 0)
        )

    with col2:
        body = st.selectbox(
            "Cuerpo" if lang == "es" else "Body",
            ["sun", "moon", "mercury", "venus", "mars",
             "jupiter", "saturn", "uranus", "neptune", "pluto"],
            format_func=lambda x: f"{get_planet_symbol(x)} {t(x)}"
        )

    if st.button("Calcular Posición" if lang == "es" else "Calculate Position"):
        dt = datetime.combine(calc_date, calc_time)
        from core.time_engine import datetime_to_jd
        from core.ephemeris import get_position

        jd = datetime_to_jd(dt)
        pos = get_position(body, jd)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Longitud" if lang == "es" else "Longitude", f"{pos.longitude_decimal:.4f}°")
        with col2:
            st.metric("Zodiacal", longitude_to_zodiacal(pos.longitude_decimal, False))
        with col3:
            st.metric("Velocidad" if lang == "es" else "Speed", f"{pos.speed_longitude:.4f}°/día" if lang == "es" else f"{pos.speed_longitude:.4f}°/day")


def get_birth_data_inputs():
    """Common birth data input widgets."""
    lang = st.session_state.lang

    col1, col2 = st.columns(2)

    with col1:
        birth_date = st.date_input(
            t("birth_date"),
            value=date(1986, 12, 5),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        birth_time = st.time_input(t("birth_time"), value=time(8, 3))
        timezone = st.selectbox(
            t("timezone"),
            ["America/Santiago", "America/New_York", "America/Buenos_Aires",
             "America/Mexico_City", "Europe/Madrid", "Europe/London",
             "Europe/Paris", "Asia/Tokyo", "UTC"],
            index=0,
        )

    with col2:
        latitude = st.number_input(
            t("latitude"),
            value=-33.4489,
            min_value=-90.0,
            max_value=90.0,
            help=t("north_positive")
        )
        longitude = st.number_input(
            t("longitude"),
            value=-70.6693,
            min_value=-180.0,
            max_value=180.0,
            help=t("east_positive")
        )
        location_name = st.text_input(
            "Nombre del lugar" if lang == "es" else "Location Name",
            value="Santiago, Chile"
        )

    return {
        "date": birth_date,
        "time": birth_time,
        "timezone": timezone,
        "latitude": latitude,
        "longitude": longitude,
        "location": location_name,
    }


def show_natal_chart():
    """Natal chart calculation page."""
    lang = st.session_state.lang

    st.title("📊 " + ("Calculadora de Carta Natal" if lang == "es" else "Natal Chart Calculator"))

    with st.expander("Datos de Nacimiento" if lang == "es" else "Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    house_system = st.selectbox(
        t("house_system"),
        list(HOUSE_SYSTEMS.keys()),
        format_func=lambda x: f"{x} - {HOUSE_SYSTEMS[x]}",
        index=0,
    )

    if st.button(t("calculate"), type="primary"):
        # Combine date and time
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])

        with st.spinner(t("calculating")):
            # Time conversion
            time_result = local_to_ut(
                birth_dt,
                birth_data["timezone"],
                birth_data["latitude"],
                birth_data["longitude"],
            )

            # Planetary positions
            positions = get_all_positions(time_result.jd_tt)

            # Houses
            houses = calculate_houses(
                time_result.jd_ut,
                birth_data["latitude"],
                birth_data["longitude"],
                house_system,
            )

            # Aspects
            positions_with_angles = dict(positions)
            positions_with_angles["ascendant"] = {"longitude_decimal": houses.ascendant}
            positions_with_angles["mc"] = {"longitude_decimal": houses.mc}
            aspects = find_all_aspects(positions_with_angles, time_result.jd_tt)

            # Store in session state
            st.session_state.natal_results = {
                "positions": positions,
                "houses": houses,
                "aspects": aspects,
                "time_result": time_result,
            }

        st.success(t("success"))

    # Display results if available
    if "natal_results" in st.session_state:
        results = st.session_state.natal_results
        positions = results["positions"]
        houses = results["houses"]
        aspects = results["aspects"]
        time_result = results["time_result"]

        # Display results in tabs
        if lang == "es":
            tab_labels = ["Posiciones", "Casas", "Aspectos", t("interpretation"), t("forecast"), "Datos Técnicos"]
        else:
            tab_labels = ["Positions", "Houses", "Aspects", t("interpretation"), t("forecast"), "Technical Data"]

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_labels)

        with tab1:
            st.subheader(t("planetary_positions"))
            pos_data = []
            for body, pos in positions.items():
                pos_data.append({
                    "Cuerpo" if lang == "es" else "Body": f"{get_planet_symbol(body)} {t(body)}",
                    "Longitud" if lang == "es" else "Longitude": f"{pos.longitude_decimal:.4f}°",
                    "Zodiacal": longitude_to_zodiacal(pos.longitude_decimal, False),
                    "Latitud" if lang == "es" else "Latitude": f"{pos.latitude_decimal:.2f}°",
                    "Velocidad" if lang == "es" else "Speed": f"{pos.speed_longitude:.3f}°/d",
                    "Retro": "℞" if pos.is_retrograde else "",
                })
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)

        with tab2:
            st.subheader(f"{t('houses')} ({HOUSE_SYSTEMS[house_system]})")

            col1, col2 = st.columns(2)
            with col1:
                st.metric(t("ascendant"), longitude_to_zodiacal(houses.ascendant, False))
            with col2:
                st.metric(t("midheaven"), longitude_to_zodiacal(houses.mc, False))

            house_data = []
            for i, cusp in enumerate(houses.cusps):
                house_data.append({
                    "Casa" if lang == "es" else "House": i + 1,
                    "Cúspide" if lang == "es" else "Cusp": f"{cusp:.2f}°",
                    "Signo" if lang == "es" else "Sign": longitude_to_zodiacal(cusp, False),
                })
            st.dataframe(pd.DataFrame(house_data), use_container_width=True)

        with tab3:
            st.subheader("Aspectos" if lang == "es" else "Aspects")
            if aspects:
                asp_data = []
                for asp in sorted(aspects, key=lambda a: a.orb):
                    asp_data.append({
                        "Cuerpo 1" if lang == "es" else "Body 1": f"{get_planet_symbol(asp.body1)} {t(asp.body1) if asp.body1 in ['sun','moon','mercury','venus','mars','jupiter','saturn','uranus','neptune','pluto'] else asp.body1.capitalize()}",
                        "Aspecto" if lang == "es" else "Aspect": t(asp.aspect_name) if asp.aspect_name in ['conjunction','opposition','trine','square','sextile'] else asp.aspect_name.capitalize(),
                        "Cuerpo 2" if lang == "es" else "Body 2": f"{get_planet_symbol(asp.body2)} {t(asp.body2) if asp.body2 in ['sun','moon','mercury','venus','mars','jupiter','saturn','uranus','neptune','pluto'] else asp.body2.capitalize()}",
                        "Orbe" if lang == "es" else "Orb": f"{asp.orb:.2f}°",
                        "Estado" if lang == "es" else "State": ("Aplicativo" if lang == "es" else "Applying") if asp.is_applying else ("Separativo" if lang == "es" else "Separating"),
                    })
                st.dataframe(pd.DataFrame(asp_data), use_container_width=True)

                # Aspect summary
                summary = calculate_aspect_summary(aspects)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total" if lang == "es" else "Total Aspects", summary["total"])
                with col2:
                    st.metric("Mayores" if lang == "es" else "Major", summary["major"])
                with col3:
                    st.metric("Menores" if lang == "es" else "Minor", summary["minor"])

        with tab4:
            # Interpretations tab
            st.subheader(t("interpretation"))
            st.markdown("---")

            main_planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

            for planet in main_planets:
                if planet in positions:
                    pos = positions[planet]
                    sign = get_sign_from_longitude(pos.longitude_decimal)
                    sign_translated = t(sign)

                    interpretation = get_planet_interpretation(planet, sign, lang)

                    if interpretation:
                        planet_name = f"{get_planet_symbol(planet)} {t(planet)}"

                        if lang == "es":
                            st.markdown(f"""
                            <div class="interpretation-box">
                                <h4>{planet_name} en {sign_translated}</h4>
                                <p>{interpretation}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="interpretation-box">
                                <h4>{planet_name} in {sign_translated}</h4>
                                <p>{interpretation}</p>
                            </div>
                            """, unsafe_allow_html=True)

        with tab5:
            # Forecast tab
            st.subheader(f"{t('forecast')} - {t('next_months')}")
            st.markdown("---")

            # Theme selector
            theme_options = {
                t("money"): "money",
                t("love"): "love",
                t("career"): "career",
                t("health"): "health",
            }

            selected_theme_label = st.selectbox(
                t("select_theme"),
                options=list(theme_options.keys()),
            )
            selected_theme = theme_options[selected_theme_label]

            st.markdown("---")

            # Get forecasts
            forecast_data = TRANSIT_INTERPRETATIONS.get(lang, {}).get(selected_theme, {})

            if forecast_data:
                for key, interpretation in list(forecast_data.items())[:4]:
                    st.markdown(f"""
                    <div class="forecast-card">
                        {interpretation}
                    </div>
                    """, unsafe_allow_html=True)

            # Personalized note
            st.markdown("---")
            sun_sign = get_sign_from_longitude(positions["sun"].longitude_decimal) if "sun" in positions else "Unknown"
            moon_sign = get_sign_from_longitude(positions["moon"].longitude_decimal) if "moon" in positions else "Unknown"

            theme_clean = selected_theme_label.split(" ", 1)[-1].lower() if " " in selected_theme_label else selected_theme_label.lower()

            if lang == "es":
                st.info(f"""
                **Nota personalizada:**
                Con tu Sol en {t(sun_sign)} y Luna en {t(moon_sign)},
                tu enfoque hacia {theme_clean} combina la energía de ambos signos.

                Los tránsitos actuales afectarán especialmente estas áreas de tu carta natal.
                Presta atención a los períodos de Luna Nueva y Luna Llena en signos compatibles
                con tu Sol y Luna natal para momentos de mayor oportunidad.
                """)
            else:
                st.info(f"""
                **Personalized note:**
                With your Sun in {t(sun_sign)} and Moon in {t(moon_sign)},
                your approach to {theme_clean} combines the energy of both signs.

                Current transits will especially affect these areas of your natal chart.
                Pay attention to New Moon and Full Moon periods in signs compatible
                with your natal Sun and Moon for moments of greater opportunity.
                """)

        with tab6:
            st.subheader("Datos de Conversión de Tiempo" if lang == "es" else "Time Conversion Data")
            time_data = time_result.to_dict()
            st.json(time_data)


def show_transits():
    """Transit analysis page."""
    lang = st.session_state.lang

    st.title("🔄 " + ("Análisis de Tránsitos" if lang == "es" else "Transit Analysis"))

    with st.expander("Datos de Nacimiento" if lang == "es" else "Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Fecha inicio" if lang == "es" else "Start Date",
            value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "Fecha fin" if lang == "es" else "End Date",
            value=date(date.today().year + 1, date.today().month, date.today().day),
        )

    transiting_bodies = st.multiselect(
        "Cuerpos en tránsito" if lang == "es" else "Transiting Bodies",
        ["jupiter", "saturn", "uranus", "neptune", "pluto"],
        default=["jupiter", "saturn", "uranus", "neptune", "pluto"],
        format_func=lambda x: f"{get_planet_symbol(x)} {t(x)}"
    )

    if st.button("Buscar Tránsitos" if lang == "es" else "Find Transits", type="primary"):
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])

        with st.spinner("Calculando carta natal..." if lang == "es" else "Calculating natal chart..."):
            time_result = local_to_ut(
                birth_dt,
                birth_data["timezone"],
                birth_data["latitude"],
                birth_data["longitude"],
            )
            positions = get_all_positions(time_result.jd_tt)
            houses = calculate_houses(
                time_result.jd_ut,
                birth_data["latitude"],
                birth_data["longitude"],
                "P",
            )

        # Build natal positions dict
        natal_positions = {}
        for body, pos in positions.items():
            natal_positions[body] = pos.longitude_decimal
        natal_positions["ascendant"] = houses.ascendant
        natal_positions["mc"] = houses.mc

        with st.spinner("Buscando tránsitos..." if lang == "es" else "Finding transits..."):
            transits_df = find_all_transits(
                natal_positions,
                datetime.combine(start_date, time(0, 0)),
                datetime.combine(end_date, time(23, 59)),
                transiting_bodies=transiting_bodies,
            )

        if not transits_df.empty:
            st.success(f"{'Encontrados' if lang == 'es' else 'Found'} {len(transits_df)} {'tránsitos' if lang == 'es' else 'transits'}")

            # Display transits
            st.dataframe(
                transits_df[["datetime_utc", "transiting_body", "aspect",
                            "natal_point", "is_retrograde"]].head(100),
                use_container_width=True,
            )

            # Timeline visualization
            st.subheader("Línea de Tiempo" if lang == "es" else "Transit Timeline")
            fig = px.scatter(
                transits_df,
                x="datetime_utc",
                y="natal_point",
                color="transiting_body",
                symbol="aspect",
                title="Tránsitos en el Tiempo" if lang == "es" else "Transits Over Time",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se encontraron tránsitos en el rango especificado." if lang == "es" else "No transits found in the specified date range.")


def show_solar_return():
    """Solar return page."""
    lang = st.session_state.lang

    st.title("🌙 " + ("Calculadora de Retorno Solar" if lang == "es" else "Solar Return Calculator"))

    with st.expander("Datos de Nacimiento" if lang == "es" else "Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    col1, col2 = st.columns(2)
    with col1:
        sr_year = st.number_input(
            "Año del Retorno Solar" if lang == "es" else "Solar Return Year",
            min_value=1900,
            max_value=2100,
            value=date.today().year,
        )
    with col2:
        sr_location = st.radio(
            "Ubicación para el Retorno" if lang == "es" else "Location for Return Chart",
            ["Lugar de Nacimiento" if lang == "es" else "Birth Location",
             "Ubicación Actual" if lang == "es" else "Current Location"],
        )

    if "Actual" in sr_location or "Current" in sr_location:
        col1, col2 = st.columns(2)
        with col1:
            sr_lat = st.number_input("Latitud RS" if lang == "es" else "SR Latitude", value=birth_data["latitude"])
        with col2:
            sr_lon = st.number_input("Longitud RS" if lang == "es" else "SR Longitude", value=birth_data["longitude"])
    else:
        sr_lat = birth_data["latitude"]
        sr_lon = birth_data["longitude"]

    if st.button("Calcular Retorno Solar" if lang == "es" else "Calculate Solar Return", type="primary"):
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])

        with st.spinner(t("calculating")):
            # Get natal Sun position
            time_result = local_to_ut(
                birth_dt,
                birth_data["timezone"],
                birth_data["latitude"],
                birth_data["longitude"],
            )
            positions = get_all_positions(time_result.jd_tt)
            natal_sun = positions["sun"].longitude_decimal

            # Calculate solar return
            sr = calculate_solar_return(
                natal_sun,
                birth_dt,
                sr_year,
                sr_lat,
                sr_lon,
                birth_data["location"],
            )

        st.success(f"Retorno Solar: {sr.exact_datetime_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"ASC {t('forecast')[:2]}" if lang == "es" else "SR Ascendant", longitude_to_zodiacal(sr.houses.ascendant, False))
        with col2:
            st.metric("MC RS" if lang == "es" else "SR MC", longitude_to_zodiacal(sr.houses.mc, False))

        # Positions
        st.subheader("Posiciones del Retorno Solar" if lang == "es" else "Solar Return Positions")
        sr_pos_data = []
        for body, pos in sr.positions.items():
            sr_pos_data.append({
                "Cuerpo" if lang == "es" else "Body": f"{get_planet_symbol(body)} {t(body)}",
                "Posición" if lang == "es" else "Position": longitude_to_zodiacal(pos.longitude_decimal, False),
                "Velocidad" if lang == "es" else "Speed": f"{pos.speed_longitude:.3f}°/d",
            })
        st.dataframe(pd.DataFrame(sr_pos_data), use_container_width=True)


def show_progressions():
    """Progressions page."""
    lang = st.session_state.lang

    st.title("📈 " + ("Progresiones Secundarias" if lang == "es" else "Secondary Progressions"))

    with st.expander("Datos de Nacimiento" if lang == "es" else "Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    target_date = st.date_input(
        "Progresar hasta" if lang == "es" else "Progress To Date",
        value=date.today()
    )

    if st.button("Calcular Progresiones" if lang == "es" else "Calculate Progressions", type="primary"):
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])
        target_dt = datetime.combine(target_date, time(12, 0))

        with st.spinner(t("calculating")):
            prog = calculate_progressions(
                birth_dt,
                birth_data["latitude"],
                birth_data["longitude"],
                target_dt,
                birth_data["timezone"],
            )

        st.success(f"{'Progresado a edad' if lang == 'es' else 'Progressed to age'} {prog.age_years:.2f} {'años' if lang == 'es' else 'years'}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("MC Progresado" if lang == "es" else "Progressed MC", f"{prog.progressed_mc:.2f}°")
        with col2:
            st.metric("ASC Progresado" if lang == "es" else "Progressed Asc", f"{prog.progressed_asc:.2f}°")

        st.subheader("Fase Lunar Progresada" if lang == "es" else "Progressed Moon Phase")
        st.metric(prog.moon_phase_name, f"{prog.moon_phase_angle:.1f}°")

        st.subheader("Posiciones Progresadas" if lang == "es" else "Progressed Positions")
        prog_data = []
        for body, pos in prog.positions.items():
            prog_data.append({
                "Cuerpo" if lang == "es" else "Body": f"{get_planet_symbol(body)} {t(body)}",
                "Natal": f"{pos.natal_longitude:.2f}°",
                "Progresado" if lang == "es" else "Progressed": f"{pos.progressed_longitude:.2f}°",
                "Movimiento" if lang == "es" else "Movement": f"{pos.movement:.2f}°",
                "Cambió Signo" if lang == "es" else "Sign Changed": "Sí" if lang == "es" and pos.sign_changed else ("Yes" if pos.sign_changed else ""),
            })
        st.dataframe(pd.DataFrame(prog_data), use_container_width=True)

        # Progressed lunar phases
        st.subheader("Fases Lunares Progresadas de por Vida" if lang == "es" else "Lifetime Progressed Lunar Phases")
        with st.spinner("Buscando fases lunares..." if lang == "es" else "Finding lunar phases..."):
            phases = find_progressed_lunar_phases(birth_dt, 0, 90)

        if phases:
            phase_data = []
            for p in phases:
                phase_data.append({
                    "Edad" if lang == "es" else "Age": f"{p.age_years:.1f}",
                    "Fecha" if lang == "es" else "Date": p.date.strftime("%Y-%m-%d"),
                    "Fase" if lang == "es" else "Phase": p.phase_name,
                })
            st.dataframe(pd.DataFrame(phase_data), use_container_width=True)


def show_ephemeris():
    """Raw ephemeris page."""
    lang = st.session_state.lang

    st.title("🪐 " + ("Explorador de Efemérides" if lang == "es" else "Ephemeris Browser"))

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Fecha inicio" if lang == "es" else "Start Date",
            value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "Fecha fin" if lang == "es" else "End Date",
            value=date(date.today().year, date.today().month + 1, date.today().day)
            if date.today().month < 12
            else date(date.today().year + 1, 1, date.today().day),
        )

    bodies = st.multiselect(
        "Cuerpos" if lang == "es" else "Bodies",
        ["sun", "moon", "mercury", "venus", "mars",
         "jupiter", "saturn", "uranus", "neptune", "pluto"],
        default=["sun", "moon", "mercury"],
        format_func=lambda x: f"{get_planet_symbol(x)} {t(x)}"
    )

    if st.button("Generar Efemérides" if lang == "es" else "Generate Ephemeris", type="primary"):
        from core.time_engine import datetime_to_jd
        from core.ephemeris import get_position

        data = []
        current = datetime.combine(start_date, time(0, 0))
        end = datetime.combine(end_date, time(0, 0))

        with st.spinner("Generando efemérides..." if lang == "es" else "Generating ephemeris..."):
            while current <= end:
                jd = datetime_to_jd(current)
                row = {"Fecha" if lang == "es" else "Date": current.strftime("%Y-%m-%d")}

                for body in bodies:
                    pos = get_position(body, jd)
                    row[f"{get_planet_symbol(body)} {t(body)}"] = longitude_to_zodiacal(
                        pos.longitude_decimal, False
                    )

                data.append(row)
                current += pd.Timedelta(days=1)

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "Descargar CSV" if lang == "es" else "Download CSV",
            csv,
            "ephemeris.csv",
            "text/csv",
        )


def show_settings():
    """Settings page."""
    lang = st.session_state.lang

    st.title("⚙️ " + ("Configuración" if lang == "es" else "Settings"))

    st.subheader("Motor de Cálculo" if lang == "es" else "Calculation Engine")

    ephemeris = EphemerisEngine()
    st.info(f"{'Método de Efemérides' if lang == 'es' else 'Ephemeris Method'}: **{ephemeris.calculation_method}**")

    if ephemeris.ephemeris_path:
        st.success(f"{'Ruta de Efemérides' if lang == 'es' else 'Ephemeris Path'}: {ephemeris.ephemeris_path}")
    else:
        if lang == "es":
            st.warning(
                "No se encontraron archivos de Swiss Ephemeris. Usando algoritmo MOSEPH. "
                "Para mayor precisión, descarga archivos .se1 a data/ephemeris/"
            )
        else:
            st.warning(
                "No Swiss Ephemeris data files found. Using MOSEPH algorithm. "
                "For higher precision, download .se1 files to data/ephemeris/"
            )

    st.subheader("Acerca de" if lang == "es" else "About")

    if lang == "es":
        st.markdown("""
        **Astro Engineering** es una herramienta de cálculo astronómico de alta precisión
        diseñada para análisis astrológico con rigor científico.

        - Usa Swiss Ephemeris para cálculos
        - Precisión: ~0.001 segundos de arco (SWIEPH) o ~0.1 segundos de arco (MOSEPH)
        - Soporta múltiples sistemas de casas
        - Conversiones completas de escalas de tiempo (UTC, TT, TDB)
        - **Interpretaciones astrológicas en español e inglés**

        Versión: 1.1.0
        """)
    else:
        st.markdown("""
        **Astro Engineering** is a high-precision astronomical calculation tool
        designed for astrological analysis with scientific rigor.

        - Uses Swiss Ephemeris for calculations
        - Precision: ~0.001 arcseconds (SWIEPH) or ~0.1 arcseconds (MOSEPH)
        - Supports multiple house systems
        - Full time scale conversions (UTC, TT, TDB)
        - **Astrological interpretations in Spanish and English**

        Version: 1.1.0
        """)


if __name__ == "__main__":
    main()
