#!/usr/bin/env python3
"""
Astro Engineering - Minimal Web App

Ultra-simple natal chart calculator.
Run with: streamlit run app_simple.py
"""

import sys
from pathlib import Path
from datetime import datetime, date, time

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from core.time_engine import local_to_ut
from core.ephemeris import get_all_positions
from core.houses import calculate_houses
from core.aspects import find_all_aspects
from data.symbols import longitude_to_zodiacal, PLANET_SYMBOLS, ZODIAC_SYMBOLS

# Page config
st.set_page_config(
    page_title="Carta Natal",
    page_icon="✨",
    layout="centered",
)

# Minimal CSS
st.markdown("""
<style>
    .main { max-width: 800px; margin: 0 auto; }
    .stButton > button { width: 100%; }
    h1 { text-align: center; color: #2E4057; }
    .planet-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("✨ Carta Natal")
st.markdown("---")

# Input form
col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        "📅 Fecha de nacimiento",
        value=date(1986, 12, 5),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
    )

with col2:
    birth_time = st.time_input(
        "🕐 Hora de nacimiento",
        value=time(8, 3),
    )

col1, col2 = st.columns(2)

with col1:
    latitude = st.number_input(
        "📍 Latitud",
        value=-33.4489,
        min_value=-90.0,
        max_value=90.0,
        format="%.4f",
        help="Norte = positivo, Sur = negativo"
    )

with col2:
    longitude = st.number_input(
        "📍 Longitud",
        value=-70.6693,
        min_value=-180.0,
        max_value=180.0,
        format="%.4f",
        help="Este = positivo, Oeste = negativo"
    )

# Common cities quick select
st.markdown("##### Ciudades comunes:")
cities = {
    "Santiago, Chile": (-33.4489, -70.6693, "America/Santiago"),
    "Buenos Aires": (-34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    "Ciudad de México": (19.4326, -99.1332, "America/Mexico_City"),
    "Madrid": (40.4168, -3.7038, "Europe/Madrid"),
    "Lima": (-12.0464, -77.0428, "America/Lima"),
    "Bogotá": (4.7110, -74.0721, "America/Bogota"),
}

city_cols = st.columns(3)
for i, (city, (lat, lon, tz)) in enumerate(cities.items()):
    with city_cols[i % 3]:
        if st.button(city, key=f"city_{i}"):
            st.session_state.lat = lat
            st.session_state.lon = lon
            st.session_state.tz = tz
            st.rerun()

# Use stored values if set
if "lat" in st.session_state:
    latitude = st.session_state.lat
if "lon" in st.session_state:
    longitude = st.session_state.lon

timezone = st.selectbox(
    "🌍 Zona horaria",
    ["America/Santiago", "America/Argentina/Buenos_Aires", "America/Mexico_City",
     "America/Lima", "America/Bogota", "America/New_York", "Europe/Madrid",
     "Europe/London", "Europe/Paris", "UTC"],
    index=0 if "tz" not in st.session_state else
          ["America/Santiago", "America/Argentina/Buenos_Aires", "America/Mexico_City",
           "America/Lima", "America/Bogota", "America/New_York", "Europe/Madrid",
           "Europe/London", "Europe/Paris", "UTC"].index(st.session_state.get("tz", "America/Santiago"))
)

st.markdown("---")

# Calculate button
if st.button("🔮 Calcular Carta Natal", type="primary"):

    birth_dt = datetime.combine(birth_date, birth_time)

    with st.spinner("Calculando posiciones planetarias..."):
        try:
            # Time conversion
            time_result = local_to_ut(birth_dt, timezone, latitude, longitude)

            # Positions
            positions = get_all_positions(time_result.jd_tt)

            # Houses
            houses = calculate_houses(time_result.jd_ut, latitude, longitude, "P")

            # Aspects
            positions_dict = dict(positions)
            positions_dict["ascendant"] = {"longitude_decimal": houses.ascendant}
            positions_dict["mc"] = {"longitude_decimal": houses.mc}
            aspects = find_all_aspects(positions_dict, time_result.jd_tt)

        except Exception as e:
            st.error(f"Error en el cálculo: {str(e)}")
            st.stop()

    # Results
    st.success("✅ Carta calculada")

    # Key angles
    st.markdown("### 🏠 Puntos Cardinales")
    col1, col2 = st.columns(2)
    with col1:
        asc = longitude_to_zodiacal(houses.ascendant, include_seconds=False)
        st.metric("Ascendente", asc)
    with col2:
        mc = longitude_to_zodiacal(houses.mc, include_seconds=False)
        st.metric("Medio Cielo", mc)

    # Planets
    st.markdown("### 🪐 Posiciones Planetarias")

    main_planets = ["sun", "moon", "mercury", "venus", "mars",
                    "jupiter", "saturn", "uranus", "neptune", "pluto"]

    planet_names = {
        "sun": "☉ Sol",
        "moon": "☽ Luna",
        "mercury": "☿ Mercurio",
        "venus": "♀ Venus",
        "mars": "♂ Marte",
        "jupiter": "♃ Júpiter",
        "saturn": "♄ Saturno",
        "uranus": "♅ Urano",
        "neptune": "♆ Neptuno",
        "pluto": "♇ Plutón",
    }

    for planet in main_planets:
        if planet in positions:
            pos = positions[planet]
            zodiac = longitude_to_zodiacal(pos.longitude_decimal, include_seconds=False)
            retro = " ℞" if pos.is_retrograde else ""

            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**{planet_names.get(planet, planet)}**{retro}")
            with col2:
                st.write(zodiac)

    # Aspects (top 10)
    st.markdown("### ✨ Aspectos Principales")

    aspect_symbols = {
        "conjunction": "☌",
        "opposition": "☍",
        "trine": "△",
        "square": "□",
        "sextile": "⚹",
    }

    major_aspects = [a for a in aspects if a.aspect_name in aspect_symbols]
    major_aspects.sort(key=lambda x: x.orb)

    for asp in major_aspects[:10]:
        symbol = aspect_symbols.get(asp.aspect_name, "•")
        b1 = planet_names.get(asp.body1, asp.body1.capitalize())
        b2 = planet_names.get(asp.body2, asp.body2.capitalize())

        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write(b1)
        with col2:
            st.write(f"{symbol}")
        with col3:
            st.write(f"{b2} ({asp.orb:.1f}°)")

    # Technical data (expandable)
    with st.expander("📊 Datos Técnicos"):
        st.write(f"**UTC:** {time_result.utc}")
        st.write(f"**Julian Day (UT):** {time_result.jd_ut:.6f}")
        st.write(f"**Delta-T:** {time_result.delta_t:.1f} segundos")
        st.write(f"**Sistema de casas:** Placidus")

        st.markdown("##### Casas:")
        for i, cusp in enumerate(houses.cusps):
            st.write(f"Casa {i+1}: {longitude_to_zodiacal(cusp, False)}")

# Footer
st.markdown("---")
st.markdown(
    "<center><small>Astro Engineering - Cálculos de alta precisión usando Swiss Ephemeris</small></center>",
    unsafe_allow_html=True
)
