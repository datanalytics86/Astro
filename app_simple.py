#!/usr/bin/env python3
"""
Astro Engineering - Web App with Interpretations

Natal chart calculator with astrological interpretations and forecasts.
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
from core.interpretations import (
    get_translation,
    get_planet_interpretation,
    get_forecast_interpretation,
    get_house_theme,
    TRANSIT_INTERPRETATIONS
)
from data.symbols import longitude_to_zodiacal, PLANET_SYMBOLS, ZODIAC_SYMBOLS

# Page config
st.set_page_config(
    page_title="Carta Natal / Birth Chart",
    page_icon="✨",
    layout="centered",
)

# Initialize session state for language
if "lang" not in st.session_state:
    st.session_state.lang = "es"

# Get current language
lang = st.session_state.lang
t = lambda key: get_translation(key, lang)

# Minimal CSS
st.markdown("""
<style>
    .main { max-width: 900px; margin: 0 auto; }
    .stButton > button { width: 100%; }
    h1 { text-align: center; color: #2E4057; }
    .planet-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
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
    }
</style>
""", unsafe_allow_html=True)

# Language toggle in sidebar
with st.sidebar:
    st.markdown(f"### {t('language')}")
    lang_options = {"Español": "es", "English": "en"}
    selected_lang = st.radio(
        "Language / Idioma",
        options=list(lang_options.keys()),
        index=0 if lang == "es" else 1,
        label_visibility="collapsed"
    )
    if lang_options[selected_lang] != lang:
        st.session_state.lang = lang_options[selected_lang]
        st.rerun()

    st.markdown("---")
    st.markdown(f"### {t('common_cities')}")
    cities = {
        "Santiago, Chile": (-33.4489, -70.6693, "America/Santiago"),
        "Buenos Aires": (-34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
        "Ciudad de México": (19.4326, -99.1332, "America/Mexico_City"),
        "Madrid": (40.4168, -3.7038, "Europe/Madrid"),
        "Lima": (-12.0464, -77.0428, "America/Lima"),
        "Bogotá": (4.7110, -74.0721, "America/Bogota"),
        "New York": (40.7128, -74.0060, "America/New_York"),
        "Los Angeles": (34.0522, -118.2437, "America/Los_Angeles"),
    }

    for city, (lat, lon, tz) in cities.items():
        if st.button(city, key=f"city_{city}"):
            st.session_state.lat = lat
            st.session_state.lon = lon
            st.session_state.tz = tz
            st.rerun()

# Title
st.title(t("title"))
st.markdown("---")

# Input form
col1, col2 = st.columns(2)

with col1:
    birth_date = st.date_input(
        t("birth_date"),
        value=date(1986, 12, 5),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
    )

with col2:
    birth_time = st.time_input(
        t("birth_time"),
        value=time(8, 3),
    )

col1, col2 = st.columns(2)

with col1:
    default_lat = st.session_state.get("lat", -33.4489)
    latitude = st.number_input(
        t("latitude"),
        value=default_lat,
        min_value=-90.0,
        max_value=90.0,
        format="%.4f",
        help=t("north_positive")
    )

with col2:
    default_lon = st.session_state.get("lon", -70.6693)
    longitude = st.number_input(
        t("longitude"),
        value=default_lon,
        min_value=-180.0,
        max_value=180.0,
        format="%.4f",
        help=t("east_positive")
    )

# Timezone
tz_list = ["America/Santiago", "America/Argentina/Buenos_Aires", "America/Mexico_City",
           "America/Lima", "America/Bogota", "America/New_York", "America/Los_Angeles",
           "Europe/Madrid", "Europe/London", "Europe/Paris", "UTC"]
default_tz = st.session_state.get("tz", "America/Santiago")
timezone = st.selectbox(
    t("timezone"),
    tz_list,
    index=tz_list.index(default_tz) if default_tz in tz_list else 0
)

st.markdown("---")

# Planet name translations
def get_planet_name(planet_key, lang):
    """Get translated planet name with symbol."""
    symbols = {
        "sun": "☉", "moon": "☽", "mercury": "☿", "venus": "♀", "mars": "♂",
        "jupiter": "♃", "saturn": "♄", "uranus": "♅", "neptune": "♆", "pluto": "♇",
    }
    name = get_translation(planet_key, lang)
    return f"{symbols.get(planet_key, '')} {name}"

def get_sign_from_longitude(longitude_deg):
    """Get zodiac sign from longitude in degrees."""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_index = int(longitude_deg / 30) % 12
    return signs[sign_index]

# Calculate button
if st.button(t("calculate"), type="primary"):

    birth_dt = datetime.combine(birth_date, birth_time)

    with st.spinner(t("calculating")):
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

            # Store results in session state
            st.session_state.results = {
                "time_result": time_result,
                "positions": positions,
                "houses": houses,
                "aspects": aspects,
            }

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

    st.success(t("success"))

# Display results if available
if "results" in st.session_state:
    results = st.session_state.results
    time_result = results["time_result"]
    positions = results["positions"]
    houses = results["houses"]
    aspects = results["aspects"]

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs([
        f"🪐 {t('planetary_positions')}",
        f"📖 {t('interpretation')}",
        f"🔮 {t('forecast')}"
    ])

    with tab1:
        # Key angles
        st.markdown(f"### {t('cardinal_points')}")
        col1, col2 = st.columns(2)
        with col1:
            asc = longitude_to_zodiacal(houses.ascendant, include_seconds=False)
            st.metric(t("ascendant"), asc)
        with col2:
            mc = longitude_to_zodiacal(houses.mc, include_seconds=False)
            st.metric(t("midheaven"), mc)

        # Planets
        st.markdown(f"### {t('planetary_positions')}")

        main_planets = ["sun", "moon", "mercury", "venus", "mars",
                        "jupiter", "saturn", "uranus", "neptune", "pluto"]

        for planet in main_planets:
            if planet in positions:
                pos = positions[planet]
                zodiac = longitude_to_zodiacal(pos.longitude_decimal, include_seconds=False)
                retro = " ℞" if pos.is_retrograde else ""

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{get_planet_name(planet, lang)}**{retro}")
                with col2:
                    st.write(zodiac)

        # Aspects (top 10)
        st.markdown(f"### {t('main_aspects')}")

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
            b1 = get_planet_name(asp.body1, lang) if asp.body1 in main_planets else asp.body1.capitalize()
            b2 = get_planet_name(asp.body2, lang) if asp.body2 in main_planets else asp.body2.capitalize()

            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.write(b1)
            with col2:
                st.write(f"{symbol}")
            with col3:
                st.write(f"{b2} ({asp.orb:.1f}°)")

        # Technical data (expandable)
        with st.expander(t("technical_data")):
            st.write(f"**UTC:** {time_result.utc}")
            st.write(f"**Julian Day (UT):** {time_result.jd_ut:.6f}")
            st.write(f"**Delta-T:** {time_result.delta_t:.1f} s")
            st.write(f"**{t('house_system')}:** Placidus")

            st.markdown(f"##### {t('houses')}:")
            for i, cusp in enumerate(houses.cusps):
                st.write(f"{t('houses')} {i+1}: {longitude_to_zodiacal(cusp, False)}")

    with tab2:
        # Interpretations for each planet
        st.markdown(f"### {t('interpretation')}")
        st.markdown("---")

        main_planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

        for planet in main_planets:
            if planet in positions:
                pos = positions[planet]
                sign = get_sign_from_longitude(pos.longitude_decimal)
                sign_translated = get_translation(sign, lang)

                interpretation = get_planet_interpretation(planet, sign, lang)

                if interpretation:
                    st.markdown(f"""
                    <div class="interpretation-box">
                        <h4>{get_planet_name(planet, lang)} en {sign_translated}</h4>
                        <p>{interpretation}</p>
                    </div>
                    """, unsafe_allow_html=True)

    with tab3:
        # Forecast section
        st.markdown(f"### {t('forecast')} - {t('next_months')}")
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

        # Get relevant forecasts based on current transits
        # For simplicity, we'll show general interpretations based on current outer planet positions
        forecast_data = TRANSIT_INTERPRETATIONS.get(lang, {}).get(selected_theme, {})

        # Display forecasts
        if forecast_data:
            for key, interpretation in list(forecast_data.items())[:4]:
                st.markdown(f"""
                <div class="forecast-card">
                    {interpretation}
                </div>
                """, unsafe_allow_html=True)

        # Additional personalized note based on natal chart
        st.markdown("---")
        sun_sign = get_sign_from_longitude(positions["sun"].longitude_decimal) if "sun" in positions else "Unknown"
        moon_sign = get_sign_from_longitude(positions["moon"].longitude_decimal) if "moon" in positions else "Unknown"

        if lang == "es":
            st.info(f"""
            **Nota personalizada:**
            Con tu Sol en {get_translation(sun_sign, lang)} y Luna en {get_translation(moon_sign, lang)},
            tu enfoque hacia {selected_theme_label.lower().replace('💰 ', '').replace('❤️ ', '').replace('💼 ', '').replace('🏥 ', '')}
            combina la energía de ambos signos.

            Los tránsitos actuales afectarán especialmente estas áreas de tu carta natal.
            Presta atención a los períodos de Luna Nueva y Luna Llena en signos compatibles
            con tu Sol y Luna natal para momentos de mayor oportunidad.
            """)
        else:
            st.info(f"""
            **Personalized note:**
            With your Sun in {get_translation(sun_sign, lang)} and Moon in {get_translation(moon_sign, lang)},
            your approach to {selected_theme_label.lower().replace('💰 ', '').replace('❤️ ', '').replace('💼 ', '').replace('🏥 ', '')}
            combines the energy of both signs.

            Current transits will especially affect these areas of your natal chart.
            Pay attention to New Moon and Full Moon periods in signs compatible
            with your natal Sun and Moon for moments of greater opportunity.
            """)

# Footer
st.markdown("---")
st.markdown(
    f"<center><small>{t('footer')}</small></center>",
    unsafe_allow_html=True
)
