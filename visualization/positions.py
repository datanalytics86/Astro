"""
Positions Module - Planetary position plots over time.

Creates plots showing planetary longitude over time, useful for
visualizing retrograde loops and transits to natal positions.
"""

from datetime import datetime, timedelta
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from core.ephemeris import get_position
from core.time_engine import datetime_to_jd
from data.symbols import ZODIAC_SIGNS, get_zodiac_sign
from visualization.styles import LIGHT_SCHEME, get_planet_color


def position_plot(
    bodies: list[str],
    start_date: datetime,
    end_date: datetime,
    natal_positions: Optional[dict] = None,
    show_retrograde: bool = True,
    resolution_days: float = 1.0,
    figsize: tuple = (14, 8),
    dpi: int = 150,
) -> plt.Figure:
    """
    Create a plot of planetary positions over time.

    Y-axis shows ecliptic longitude (0-360), X-axis shows time.
    Horizontal lines can mark natal positions for transit visualization.

    Args:
        bodies: List of bodies to plot
        start_date: Start of time range
        end_date: End of time range
        natal_positions: Dictionary of point name -> longitude for horizontal markers
        show_retrograde: Whether to highlight retrograde periods
        resolution_days: Time step for position calculation
        figsize: Figure size
        dpi: Resolution

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Generate dates
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=resolution_days)

    # Plot each body
    for body in bodies:
        positions = []
        speeds = []

        for date in dates:
            jd = datetime_to_jd(date)
            pos = get_position(body, jd)
            positions.append(pos.longitude_decimal)
            speeds.append(pos.speed_longitude)

        # Convert to arrays
        y = np.array(positions)
        speed = np.array(speeds)

        color = get_planet_color(body, LIGHT_SCHEME)

        # Handle longitude wrapping (0/360 discontinuity)
        # Break line where jump > 180 degrees
        jumps = np.abs(np.diff(y)) > 180
        y_masked = np.ma.array(y)
        y_masked[1:][jumps] = np.ma.masked

        # Plot main line
        ax.plot(dates, y_masked, color=color, label=body.capitalize(), linewidth=1.5)

        # Highlight retrograde periods
        if show_retrograde:
            retro_mask = speed < 0
            retro_dates = [d for d, r in zip(dates, retro_mask) if r]
            retro_pos = [p for p, r in zip(y, retro_mask) if r]

            if retro_dates:
                ax.scatter(
                    retro_dates,
                    retro_pos,
                    color=color,
                    s=3,
                    alpha=0.5,
                    marker=".",
                )

    # Add natal position lines
    if natal_positions:
        for point, lon in natal_positions.items():
            if hasattr(lon, "longitude_decimal"):
                lon = lon.longitude_decimal
            elif isinstance(lon, dict):
                lon = lon.get("longitude_decimal", lon.get("longitude", 0))

            ax.axhline(
                y=lon,
                color="gray",
                linestyle="--",
                alpha=0.5,
                linewidth=1,
            )
            ax.text(
                dates[-1],
                lon,
                f"  {point.capitalize()} ({lon:.1f}°)",
                va="center",
                fontsize=8,
                color="gray",
            )

    # Add zodiac sign bands
    for i, sign in enumerate(ZODIAC_SIGNS):
        start_deg = i * 30
        end_deg = (i + 1) * 30

        color = "#F5F5F5" if i % 2 == 0 else "#FFFFFF"
        ax.axhspan(start_deg, end_deg, facecolor=color, alpha=0.3)

        # Add sign label on right
        ax.text(
            dates[-1],
            start_deg + 15,
            f"  {sign[:3]}",
            va="center",
            fontsize=7,
            color="gray",
        )

    # Formatting
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, 360)
    ax.set_xlabel("Date")
    ax.set_ylabel("Ecliptic Longitude (degrees)")
    ax.set_title("Planetary Positions Over Time")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # Y-axis ticks at sign boundaries
    ax.set_yticks(range(0, 361, 30))
    ax.set_yticklabels([f"{d}°" for d in range(0, 361, 30)])

    plt.tight_layout()
    return fig


def retrograde_loops(
    body: str,
    start_date: datetime,
    end_date: datetime,
    natal_position: Optional[float] = None,
    figsize: tuple = (12, 6),
    dpi: int = 150,
) -> plt.Figure:
    """
    Create a detailed view of retrograde loops for a single body.

    Shows the characteristic loop pattern as a planet stations and
    retrogrades.

    Args:
        body: Body to plot
        start_date: Start date
        end_date: End date
        natal_position: Optional natal point to highlight
        figsize: Figure size
        dpi: Resolution

    Returns:
        matplotlib Figure
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=dpi, sharex=True)

    # Generate high-resolution data
    dates = []
    positions = []
    speeds = []

    current = start_date
    while current <= end_date:
        dates.append(current)
        jd = datetime_to_jd(current)
        pos = get_position(body, jd)
        positions.append(pos.longitude_decimal)
        speeds.append(pos.speed_longitude)
        current += timedelta(days=0.5)  # High resolution

    y = np.array(positions)
    speed = np.array(speeds)

    color = get_planet_color(body, LIGHT_SCHEME)

    # Top plot: Position
    # Handle wrapping
    jumps = np.abs(np.diff(y)) > 180
    y_masked = np.ma.array(y)
    y_masked[1:][jumps] = np.ma.masked

    ax1.plot(dates, y_masked, color=color, linewidth=1.5)

    # Highlight retrograde
    retro_mask = speed < 0
    for i in range(len(dates) - 1):
        if retro_mask[i]:
            ax1.axvspan(dates[i], dates[i + 1], alpha=0.2, color=color)

    # Add natal position line
    if natal_position is not None:
        ax1.axhline(y=natal_position, color="red", linestyle="--", alpha=0.7)
        ax1.text(
            dates[0],
            natal_position,
            f"Natal ({natal_position:.1f}°)",
            va="bottom",
            fontsize=8,
            color="red",
        )

    ax1.set_ylabel("Longitude (°)")
    ax1.set_title(f"{body.capitalize()} Position and Speed")
    ax1.grid(True, alpha=0.3)

    # Bottom plot: Speed
    ax2.plot(dates, speed, color=color, linewidth=1)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax2.fill_between(dates, speed, 0, where=speed < 0, alpha=0.3, color=color)

    ax2.set_ylabel("Speed (°/day)")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)

    # Mark stations (speed = 0)
    stations = []
    for i in range(1, len(speed)):
        if speed[i - 1] * speed[i] < 0:  # Sign change
            stations.append(dates[i])
            station_type = "R" if speed[i - 1] > 0 else "D"
            ax2.axvline(x=dates[i], color="gray", linestyle=":", alpha=0.7)
            ax2.text(
                dates[i],
                ax2.get_ylim()[1],
                station_type,
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

    plt.tight_layout()
    return fig


def aspect_approach_chart(
    transiting_body: str,
    natal_position: float,
    aspect_angle: float,
    start_date: datetime,
    end_date: datetime,
    orb: float = 3.0,
    figsize: tuple = (12, 5),
    dpi: int = 150,
) -> plt.Figure:
    """
    Show approach to exact aspect over time.

    Plots the orb (distance from exact aspect) over time.

    Args:
        transiting_body: Transiting body name
        natal_position: Natal point longitude
        aspect_angle: Aspect angle (0, 60, 90, etc.)
        start_date: Start date
        end_date: End date
        orb: Maximum orb to show
        figsize: Figure size
        dpi: Resolution

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    dates = []
    orbs = []

    current = start_date
    while current <= end_date:
        dates.append(current)
        jd = datetime_to_jd(current)
        pos = get_position(transiting_body, jd)

        # Calculate orb
        target = (natal_position + aspect_angle) % 360
        diff = abs(pos.longitude_decimal - target)
        if diff > 180:
            diff = 360 - diff
        orbs.append(diff)

        current += timedelta(days=1)

    orb_arr = np.array(orbs)
    color = get_planet_color(transiting_body, LIGHT_SCHEME)

    # Plot orb
    ax.plot(dates, orb_arr, color=color, linewidth=1.5)

    # Fill area within orb
    ax.fill_between(
        dates,
        orb_arr,
        orb,
        where=orb_arr <= orb,
        alpha=0.3,
        color=color,
    )

    # Mark exact aspects (orb = 0)
    for i in range(1, len(orbs)):
        if orbs[i - 1] > orbs[i] < orbs[min(i + 1, len(orbs) - 1)]:
            # Local minimum
            if orbs[i] < 0.5:  # Near exact
                ax.axvline(x=dates[i], color="red", linestyle="--", alpha=0.7)
                ax.text(
                    dates[i],
                    orbs[i],
                    f"\n{dates[i].strftime('%Y-%m-%d')}",
                    ha="center",
                    va="top",
                    fontsize=8,
                    color="red",
                )

    ax.axhline(y=orb, color="gray", linestyle=":", label=f"Orb limit ({orb}°)")
    ax.axhline(y=0, color="black", linewidth=0.5)

    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, min(max(orbs) + 1, 15))
    ax.set_xlabel("Date")
    ax.set_ylabel("Orb (degrees from exact)")
    ax.set_title(f"{transiting_body.capitalize()} approaching aspect ({aspect_angle}°)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
