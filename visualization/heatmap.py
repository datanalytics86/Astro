"""
Heatmap Module - Activation heatmap visualization.

Creates calendar-style heatmaps showing transit activation intensity.
"""

from datetime import datetime, timedelta
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd


def activation_heatmap(
    activation_data: pd.DataFrame,
    natal_points: list[str],
    start_date: datetime,
    end_date: datetime,
    resolution: str = "week",
    cmap: str = "YlOrRd",
    figsize: tuple = (14, 6),
    dpi: int = 150,
) -> plt.Figure:
    """
    Create an activation heatmap.

    Args:
        activation_data: DataFrame from ActivationEngine with date and activation columns
        natal_points: Which natal points to include
        start_date: Start of visualization
        end_date: End of visualization
        resolution: Time resolution ('day', 'week', 'month')
        cmap: Matplotlib colormap name
        figsize: Figure size
        dpi: Resolution

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Filter and prepare data
    df = activation_data.copy()
    if "date" in df.columns:
        if df["date"].dtype == object:
            df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    else:
        return fig  # No data

    # Get activation columns for requested points
    activation_cols = []
    for point in natal_points:
        col = f"{point}_activation"
        if col in df.columns:
            activation_cols.append(col)

    if not activation_cols:
        ax.text(
            0.5,
            0.5,
            "No activation data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        return fig

    # Aggregate by resolution
    if resolution == "week":
        df["period"] = df["date"].dt.to_period("W").dt.start_time
    elif resolution == "month":
        df["period"] = df["date"].dt.to_period("M").dt.start_time
    else:  # day
        df["period"] = df["date"]

    # Group and average
    grouped = df.groupby("period")[activation_cols].mean()

    # Create heatmap data
    periods = grouped.index.tolist()
    points = [col.replace("_activation", "") for col in activation_cols]

    data = grouped.values.T  # Points x Periods

    # Create heatmap
    im = ax.imshow(
        data,
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=1,
        interpolation="nearest",
    )

    # Labels
    ax.set_yticks(range(len(points)))
    ax.set_yticklabels([p.capitalize() for p in points])

    # X-axis labels (show subset)
    n_periods = len(periods)
    if n_periods > 20:
        step = n_periods // 10
        tick_positions = range(0, n_periods, step)
    else:
        tick_positions = range(n_periods)

    ax.set_xticks(list(tick_positions))
    ax.set_xticklabels(
        [periods[i].strftime("%Y-%m-%d") for i in tick_positions],
        rotation=45,
        ha="right",
    )

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, label="Activation Level")

    # Title
    ax.set_title(f"Transit Activation Heatmap ({resolution}ly)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Natal Point")

    plt.tight_layout()
    return fig


def calendar_heatmap(
    activation_data: pd.DataFrame,
    year: int,
    point: str = "total",
    cmap: str = "YlOrRd",
    figsize: tuple = (16, 8),
    dpi: int = 150,
) -> plt.Figure:
    """
    Create a calendar-style heatmap for a single year.

    Shows all days of the year with activation levels.

    Args:
        activation_data: DataFrame with date and activation columns
        year: Year to display
        point: Which point to show (or 'total' for max_activation)
        cmap: Colormap
        figsize: Figure size
        dpi: Resolution

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Prepare data
    df = activation_data.copy()
    if df["date"].dtype == object:
        df["date"] = pd.to_datetime(df["date"])

    # Filter to year
    df = df[df["date"].dt.year == year]

    if df.empty:
        ax.text(
            0.5,
            0.5,
            f"No data for {year}",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        return fig

    # Get activation column
    if point == "total":
        col = "max_activation" if "max_activation" in df.columns else "mean_activation"
    else:
        col = f"{point}_activation"

    if col not in df.columns:
        col = df.columns[1]  # First activation column

    # Create calendar data
    df["week"] = df["date"].dt.isocalendar().week
    df["dayofweek"] = df["date"].dt.dayofweek  # Monday = 0

    # Pivot for heatmap (week x day_of_week)
    pivot = df.pivot_table(index="dayofweek", columns="week", values=col, aggfunc="mean")

    # Fill missing weeks
    all_weeks = range(1, 54)
    for w in all_weeks:
        if w not in pivot.columns:
            pivot[w] = np.nan
    pivot = pivot.reindex(columns=sorted(pivot.columns))

    # Plot
    im = ax.imshow(
        pivot.values,
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=1,
    )

    # Y-axis (days of week)
    ax.set_yticks(range(7))
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

    # X-axis (months)
    month_starts = []
    for month in range(1, 13):
        first_day = datetime(year, month, 1)
        week = first_day.isocalendar()[1]
        month_starts.append((week, first_day.strftime("%b")))

    ax.set_xticks([m[0] for m in month_starts])
    ax.set_xticklabels([m[1] for m in month_starts])

    # Colorbar
    plt.colorbar(im, ax=ax, label="Activation")

    ax.set_title(f"Transit Activation Calendar - {year}")
    ax.invert_yaxis()

    plt.tight_layout()
    return fig


def monthly_summary_heatmap(
    activation_data: pd.DataFrame,
    natal_points: list[str],
    years: list[int],
    cmap: str = "YlOrRd",
    figsize: tuple = (14, 8),
    dpi: int = 150,
) -> plt.Figure:
    """
    Create a heatmap showing monthly averages across years.

    Args:
        activation_data: DataFrame with activation data
        natal_points: Points to include
        years: Years to include
        cmap: Colormap
        figsize: Figure size
        dpi: Resolution

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    df = activation_data.copy()
    if df["date"].dtype == object:
        df["date"] = pd.to_datetime(df["date"])

    # Filter years
    df = df[df["date"].dt.year.isin(years)]

    # Add year-month column
    df["year_month"] = df["date"].dt.to_period("M")

    # Get relevant columns
    cols = []
    for point in natal_points:
        col = f"{point}_activation"
        if col in df.columns:
            cols.append(col)

    if not cols:
        return fig

    # Create max activation per month
    df["max_activation"] = df[cols].max(axis=1)

    # Pivot: year x month
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    pivot = df.pivot_table(
        index="year",
        columns="month",
        values="max_activation",
        aggfunc="mean",
    )

    # Plot
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)

    # Labels
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    ax.set_xticks(range(12))
    ax.set_xticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )

    plt.colorbar(im, ax=ax, label="Avg. Activation")

    ax.set_title("Monthly Transit Activation Summary")
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")

    plt.tight_layout()
    return fig
