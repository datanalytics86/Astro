"""
Timeline Module - Transit timeline visualization.

Creates interactive timeline visualizations showing transit activity
over time using Plotly for interactivity.
"""

from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.symbols import PLANET_NAMES, ASPECT_SYMBOLS
from visualization.styles import LIGHT_SCHEME, get_planet_color, get_aspect_color


def transit_timeline(
    transits_df: pd.DataFrame,
    natal_positions: dict,
    start_date: datetime,
    end_date: datetime,
    group_by: str = "natal_point",
    show_orb_bands: bool = True,
    highlight_exact: bool = True,
    orb_days: int = 14,
) -> go.Figure:
    """
    Create an interactive transit timeline.

    Args:
        transits_df: DataFrame from TransitFinder.find_all_transits()
        natal_positions: Dictionary of natal point positions
        start_date: Start of timeline
        end_date: End of timeline
        group_by: How to group transits ('natal_point' or 'transiting_body')
        show_orb_bands: Whether to show orb bands around exact dates
        highlight_exact: Whether to highlight exact transit dates
        orb_days: Width of orb bands in days

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    if transits_df.empty:
        fig.add_annotation(
            text="No transits found in date range",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    # Prepare data
    df = transits_df.copy()

    # Parse datetime if string
    if df["datetime_utc"].dtype == object:
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])

    # Get unique categories for y-axis
    if group_by == "natal_point":
        categories = df["natal_point"].unique().tolist()
        category_col = "natal_point"
        color_col = "transiting_body"
    else:
        categories = df["transiting_body"].unique().tolist()
        category_col = "transiting_body"
        color_col = "natal_point"

    # Create y-axis mapping
    y_map = {cat: i for i, cat in enumerate(categories)}

    # Add orb bands if requested
    if show_orb_bands:
        for _, row in df.iterrows():
            dt = row["datetime_utc"]
            y_val = y_map.get(row[category_col], 0)

            # Calculate orb band width
            start_band = dt - pd.Timedelta(days=orb_days)
            end_band = dt + pd.Timedelta(days=orb_days)

            # Get color based on transiting body
            color = get_planet_color(
                row["transiting_body"], LIGHT_SCHEME
            )

            fig.add_shape(
                type="rect",
                x0=start_band,
                x1=end_band,
                y0=y_val - 0.3,
                y1=y_val + 0.3,
                fillcolor=color,
                opacity=0.15,
                line_width=0,
            )

    # Add exact transit markers
    for _, row in df.iterrows():
        dt = row["datetime_utc"]
        y_val = y_map.get(row[category_col], 0)
        is_retro = row.get("is_retrograde", False)

        color = get_planet_color(row["transiting_body"], LIGHT_SCHEME)
        aspect_symbol = ASPECT_SYMBOLS.get(row["aspect"], row["aspect"][:3])

        # Marker symbol based on retrograde
        marker_symbol = "diamond" if is_retro else "circle"

        # Hover text
        hover = (
            f"<b>{row['transiting_body'].capitalize()} "
            f"{aspect_symbol} {row['natal_point'].capitalize()}</b><br>"
            f"Date: {dt.strftime('%Y-%m-%d %H:%M')}<br>"
            f"Aspect: {row['aspect']}<br>"
            f"Pass: {row.get('pass_number', 1)}<br>"
            f"{'Retrograde' if is_retro else 'Direct'}"
        )

        fig.add_trace(
            go.Scatter(
                x=[dt],
                y=[y_val],
                mode="markers",
                marker=dict(
                    size=12 if highlight_exact else 8,
                    color=color,
                    symbol=marker_symbol,
                    line=dict(color="white", width=1),
                ),
                name=f"{row['transiting_body']} {aspect_symbol} {row['natal_point']}",
                hovertemplate=hover,
                showlegend=False,
            )
        )

    # Update layout
    fig.update_layout(
        title="Transit Timeline",
        xaxis_title="Date",
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(categories))),
            ticktext=[c.capitalize() for c in categories],
        ),
        xaxis=dict(
            range=[start_date, end_date],
            rangeslider=dict(visible=True),
            type="date",
        ),
        height=max(400, 100 + 50 * len(categories)),
        hovermode="closest",
        showlegend=False,
    )

    return fig


def multi_body_timeline(
    transits_df: pd.DataFrame,
    bodies: list[str],
    start_date: datetime,
    end_date: datetime,
) -> go.Figure:
    """
    Create a timeline with separate rows for each transiting body.

    Args:
        transits_df: Transit data
        bodies: List of transiting bodies to show
        start_date: Start date
        end_date: End date

    Returns:
        Plotly Figure with subplots
    """
    fig = make_subplots(
        rows=len(bodies),
        cols=1,
        shared_xaxes=True,
        subplot_titles=[b.capitalize() for b in bodies],
        vertical_spacing=0.05,
    )

    df = transits_df.copy()
    if df["datetime_utc"].dtype == object:
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])

    for i, body in enumerate(bodies, 1):
        body_df = df[df["transiting_body"] == body]

        if body_df.empty:
            continue

        color = get_planet_color(body, LIGHT_SCHEME)

        for _, row in body_df.iterrows():
            aspect_symbol = ASPECT_SYMBOLS.get(row["aspect"], "?")

            fig.add_trace(
                go.Scatter(
                    x=[row["datetime_utc"]],
                    y=[row["natal_point"]],
                    mode="markers+text",
                    marker=dict(size=10, color=color),
                    text=aspect_symbol,
                    textposition="top center",
                    name=f"{body} {row['aspect']} {row['natal_point']}",
                    showlegend=False,
                    hovertemplate=(
                        f"{body.capitalize()} {aspect_symbol} "
                        f"{row['natal_point'].capitalize()}<br>"
                        f"%{{x|%Y-%m-%d}}<extra></extra>"
                    ),
                ),
                row=i,
                col=1,
            )

    fig.update_xaxes(range=[start_date, end_date])
    fig.update_layout(
        height=200 * len(bodies),
        title="Transit Timeline by Planet",
        showlegend=False,
    )

    return fig


def create_transit_gantt(
    transit_windows: list[dict],
    start_date: datetime,
    end_date: datetime,
) -> go.Figure:
    """
    Create a Gantt-style chart showing transit activity windows.

    Args:
        transit_windows: List of windows from TransitTimeline.find_transit_windows()
        start_date: Chart start date
        end_date: Chart end date

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for window in transit_windows:
        fig.add_trace(
            go.Bar(
                x=[(window["end"] - window["start"]).days],
                y=[window.get("aspect", "Transit")],
                orientation="h",
                base=window["start"],
                marker_color=get_aspect_color(
                    window.get("aspect", "conjunction"), LIGHT_SCHEME
                ),
                hovertemplate=(
                    f"Aspect: {window.get('aspect', 'Transit')}<br>"
                    f"Start: {window['start'].strftime('%Y-%m-%d')}<br>"
                    f"End: {window['end'].strftime('%Y-%m-%d')}<br>"
                    f"Peak: {window.get('peak_date', window['start']).strftime('%Y-%m-%d')}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Transit Activity Windows",
        xaxis_title="Date",
        yaxis_title="Aspect",
        xaxis=dict(range=[start_date, end_date], type="date"),
        barmode="stack",
        height=400,
    )

    return fig
