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
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""

    # Sidebar navigation
    st.sidebar.title("🔭 Astro Engineering")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "📊 Natal Chart",
            "🔄 Transits",
            "🌙 Solar Return",
            "📈 Progressions",
            "🪐 Ephemeris",
            "⚙️ Settings",
        ],
    )

    # Route to appropriate page
    if page == "🏠 Home":
        show_home()
    elif page == "📊 Natal Chart":
        show_natal_chart()
    elif page == "🔄 Transits":
        show_transits()
    elif page == "🌙 Solar Return":
        show_solar_return()
    elif page == "📈 Progressions":
        show_progressions()
    elif page == "🪐 Ephemeris":
        show_ephemeris()
    elif page == "⚙️ Settings":
        show_settings()


def show_home():
    """Home page with overview."""
    st.markdown('<p class="main-header">Astro Engineering</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">High-Precision Astronomical Calculations for Astrological Analysis</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🎯 Precision")
        st.markdown("""
        - Swiss Ephemeris calculations
        - ~0.001 arcsecond accuracy
        - Multiple house systems
        - Validated against JPL Horizons
        """)

    with col2:
        st.markdown("### 📊 Features")
        st.markdown("""
        - Natal chart calculation
        - Transit analysis
        - Solar returns
        - Secondary progressions
        - Aspect detection
        """)

    with col3:
        st.markdown("### 🔧 Technical")
        st.markdown("""
        - Time scale conversions
        - Delta-T calculations
        - Retrograde detection
        - Export to JSON/iCal
        """)

    st.markdown("---")

    # Quick calculator
    st.subheader("Quick Position Calculator")

    col1, col2 = st.columns(2)

    with col1:
        calc_date = st.date_input("Date", value=date.today())
        calc_time = st.time_input("Time (UTC)", value=time(12, 0))

    with col2:
        body = st.selectbox(
            "Body",
            ["sun", "moon", "mercury", "venus", "mars",
             "jupiter", "saturn", "uranus", "neptune", "pluto"],
        )

    if st.button("Calculate Position"):
        dt = datetime.combine(calc_date, calc_time)
        from core.time_engine import datetime_to_jd
        from core.ephemeris import get_position

        jd = datetime_to_jd(dt)
        pos = get_position(body, jd)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Longitude", f"{pos.longitude_decimal:.4f}°")
        with col2:
            st.metric("Zodiacal", longitude_to_zodiacal(pos.longitude_decimal, False))
        with col3:
            st.metric("Speed", f"{pos.speed_longitude:.4f}°/day")


def get_birth_data_inputs():
    """Common birth data input widgets."""
    col1, col2 = st.columns(2)

    with col1:
        birth_date = st.date_input(
            "Birth Date",
            value=date(1986, 12, 5),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        birth_time = st.time_input("Birth Time", value=time(8, 3))
        timezone = st.selectbox(
            "Timezone",
            ["America/Santiago", "America/New_York", "Europe/London",
             "Europe/Paris", "Asia/Tokyo", "UTC"],
            index=0,
        )

    with col2:
        latitude = st.number_input("Latitude", value=-33.4489, min_value=-90.0, max_value=90.0)
        longitude = st.number_input("Longitude", value=-70.6693, min_value=-180.0, max_value=180.0)
        location_name = st.text_input("Location Name", value="Santiago, Chile")

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
    st.title("📊 Natal Chart Calculator")

    with st.expander("Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    house_system = st.selectbox(
        "House System",
        list(HOUSE_SYSTEMS.keys()),
        format_func=lambda x: f"{x} - {HOUSE_SYSTEMS[x]}",
        index=0,
    )

    if st.button("Calculate Chart", type="primary"):
        # Combine date and time
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])

        with st.spinner("Calculating..."):
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

        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Positions", "Houses", "Aspects", "Time Data"]
        )

        with tab1:
            st.subheader("Planetary Positions")
            pos_data = []
            for body, pos in positions.items():
                pos_data.append({
                    "Body": body.capitalize(),
                    "Longitude": f"{pos.longitude_decimal:.4f}°",
                    "Zodiacal": longitude_to_zodiacal(pos.longitude_decimal, False),
                    "Latitude": f"{pos.latitude_decimal:.2f}°",
                    "Speed": f"{pos.speed_longitude:.3f}°/d",
                    "Retrograde": "R" if pos.is_retrograde else "",
                })
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)

        with tab2:
            st.subheader(f"House Cusps ({HOUSE_SYSTEMS[house_system]})")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Ascendant", longitude_to_zodiacal(houses.ascendant, False))
            with col2:
                st.metric("Midheaven", longitude_to_zodiacal(houses.mc, False))

            house_data = []
            for i, cusp in enumerate(houses.cusps):
                house_data.append({
                    "House": i + 1,
                    "Cusp": f"{cusp:.2f}°",
                    "Sign": longitude_to_zodiacal(cusp, False),
                })
            st.dataframe(pd.DataFrame(house_data), use_container_width=True)

        with tab3:
            st.subheader("Aspects")
            if aspects:
                asp_data = []
                for asp in sorted(aspects, key=lambda a: a.orb):
                    asp_data.append({
                        "Body 1": asp.body1.capitalize(),
                        "Aspect": asp.aspect_name.capitalize(),
                        "Body 2": asp.body2.capitalize(),
                        "Orb": f"{asp.orb:.2f}°",
                        "State": "Applying" if asp.is_applying else "Separating",
                    })
                st.dataframe(pd.DataFrame(asp_data), use_container_width=True)

                # Aspect summary
                summary = calculate_aspect_summary(aspects)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Aspects", summary["total"])
                with col2:
                    st.metric("Major", summary["major"])
                with col3:
                    st.metric("Minor", summary["minor"])

        with tab4:
            st.subheader("Time Conversion Data")
            time_data = time_result.to_dict()
            st.json(time_data)


def show_transits():
    """Transit analysis page."""
    st.title("🔄 Transit Analysis")

    with st.expander("Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today())
    with col2:
        end_date = st.date_input(
            "End Date",
            value=date(date.today().year + 1, date.today().month, date.today().day),
        )

    transiting_bodies = st.multiselect(
        "Transiting Bodies",
        ["jupiter", "saturn", "uranus", "neptune", "pluto"],
        default=["jupiter", "saturn", "uranus", "neptune", "pluto"],
    )

    if st.button("Find Transits", type="primary"):
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])

        with st.spinner("Calculating natal chart..."):
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

        with st.spinner("Finding transits..."):
            transits_df = find_all_transits(
                natal_positions,
                datetime.combine(start_date, time(0, 0)),
                datetime.combine(end_date, time(23, 59)),
                transiting_bodies=transiting_bodies,
            )

        if not transits_df.empty:
            st.success(f"Found {len(transits_df)} transits")

            # Display transits
            st.dataframe(
                transits_df[["datetime_utc", "transiting_body", "aspect",
                            "natal_point", "is_retrograde"]].head(100),
                use_container_width=True,
            )

            # Timeline visualization
            st.subheader("Transit Timeline")
            fig = px.scatter(
                transits_df,
                x="datetime_utc",
                y="natal_point",
                color="transiting_body",
                symbol="aspect",
                title="Transits Over Time",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No transits found in the specified date range.")


def show_solar_return():
    """Solar return page."""
    st.title("🌙 Solar Return Calculator")

    with st.expander("Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    col1, col2 = st.columns(2)
    with col1:
        sr_year = st.number_input(
            "Solar Return Year",
            min_value=1900,
            max_value=2100,
            value=date.today().year,
        )
    with col2:
        sr_location = st.radio(
            "Location for Return Chart",
            ["Birth Location", "Current Location"],
        )

    if sr_location == "Current Location":
        col1, col2 = st.columns(2)
        with col1:
            sr_lat = st.number_input("SR Latitude", value=birth_data["latitude"])
        with col2:
            sr_lon = st.number_input("SR Longitude", value=birth_data["longitude"])
    else:
        sr_lat = birth_data["latitude"]
        sr_lon = birth_data["longitude"]

    if st.button("Calculate Solar Return", type="primary"):
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])

        with st.spinner("Calculating..."):
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

        st.success(f"Solar Return: {sr.exact_datetime_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("SR Ascendant", longitude_to_zodiacal(sr.houses.ascendant, False))
        with col2:
            st.metric("SR MC", longitude_to_zodiacal(sr.houses.mc, False))

        # Positions
        st.subheader("Solar Return Positions")
        sr_pos_data = []
        for body, pos in sr.positions.items():
            sr_pos_data.append({
                "Body": body.capitalize(),
                "Position": longitude_to_zodiacal(pos.longitude_decimal, False),
                "Speed": f"{pos.speed_longitude:.3f}°/d",
            })
        st.dataframe(pd.DataFrame(sr_pos_data), use_container_width=True)


def show_progressions():
    """Progressions page."""
    st.title("📈 Secondary Progressions")

    with st.expander("Birth Data", expanded=True):
        birth_data = get_birth_data_inputs()

    target_date = st.date_input("Progress To Date", value=date.today())

    if st.button("Calculate Progressions", type="primary"):
        birth_dt = datetime.combine(birth_data["date"], birth_data["time"])
        target_dt = datetime.combine(target_date, time(12, 0))

        with st.spinner("Calculating..."):
            prog = calculate_progressions(
                birth_dt,
                birth_data["latitude"],
                birth_data["longitude"],
                target_dt,
                birth_data["timezone"],
            )

        st.success(f"Progressed to age {prog.age_years:.2f} years")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Progressed MC", f"{prog.progressed_mc:.2f}°")
        with col2:
            st.metric("Progressed Asc", f"{prog.progressed_asc:.2f}°")

        st.subheader("Progressed Moon Phase")
        st.metric(prog.moon_phase_name, f"{prog.moon_phase_angle:.1f}°")

        st.subheader("Progressed Positions")
        prog_data = []
        for body, pos in prog.positions.items():
            prog_data.append({
                "Body": body.capitalize(),
                "Natal": f"{pos.natal_longitude:.2f}°",
                "Progressed": f"{pos.progressed_longitude:.2f}°",
                "Movement": f"{pos.movement:.2f}°",
                "Sign Changed": "Yes" if pos.sign_changed else "",
            })
        st.dataframe(pd.DataFrame(prog_data), use_container_width=True)

        # Progressed lunar phases
        st.subheader("Lifetime Progressed Lunar Phases")
        with st.spinner("Finding lunar phases..."):
            phases = find_progressed_lunar_phases(birth_dt, 0, 90)

        if phases:
            phase_data = []
            for p in phases:
                phase_data.append({
                    "Age": f"{p.age_years:.1f}",
                    "Date": p.date.strftime("%Y-%m-%d"),
                    "Phase": p.phase_name,
                })
            st.dataframe(pd.DataFrame(phase_data), use_container_width=True)


def show_ephemeris():
    """Raw ephemeris page."""
    st.title("🪐 Ephemeris Browser")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today())
    with col2:
        end_date = st.date_input(
            "End Date",
            value=date(date.today().year, date.today().month + 1, date.today().day)
            if date.today().month < 12
            else date(date.today().year + 1, 1, date.today().day),
        )

    bodies = st.multiselect(
        "Bodies",
        ["sun", "moon", "mercury", "venus", "mars",
         "jupiter", "saturn", "uranus", "neptune", "pluto"],
        default=["sun", "moon", "mercury"],
    )

    if st.button("Generate Ephemeris", type="primary"):
        from core.time_engine import datetime_to_jd
        from core.ephemeris import get_position

        data = []
        current = datetime.combine(start_date, time(0, 0))
        end = datetime.combine(end_date, time(0, 0))

        with st.spinner("Generating ephemeris..."):
            while current <= end:
                jd = datetime_to_jd(current)
                row = {"Date": current.strftime("%Y-%m-%d")}

                for body in bodies:
                    pos = get_position(body, jd)
                    row[body.capitalize()] = longitude_to_zodiacal(
                        pos.longitude_decimal, False
                    )

                data.append(row)
                current += pd.Timedelta(days=1)

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "ephemeris.csv",
            "text/csv",
        )


def show_settings():
    """Settings page."""
    st.title("⚙️ Settings")

    st.subheader("Calculation Engine")

    ephemeris = EphemerisEngine()
    st.info(f"Ephemeris Method: **{ephemeris.calculation_method}**")

    if ephemeris.ephemeris_path:
        st.success(f"Ephemeris Path: {ephemeris.ephemeris_path}")
    else:
        st.warning(
            "No Swiss Ephemeris data files found. Using MOSEPH algorithm. "
            "For higher precision, download .se1 files to data/ephemeris/"
        )

    st.subheader("About")
    st.markdown("""
    **Astro Engineering** is a high-precision astronomical calculation tool
    designed for astrological analysis with scientific rigor.

    - Uses Swiss Ephemeris for calculations
    - Precision: ~0.001 arcseconds (SWIEPH) or ~0.1 arcseconds (MOSEPH)
    - Supports multiple house systems
    - Full time scale conversions (UTC, TT, TDB)

    Version: 1.0.0
    """)


if __name__ == "__main__":
    main()
