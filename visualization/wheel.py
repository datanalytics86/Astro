"""
Wheel Module - Natal chart wheel visualization.

Creates circular chart representations with planets, houses, and aspects.
"""

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Wedge, FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np

from data.symbols import (
    ZODIAC_SYMBOLS,
    ZODIAC_SIGNS,
    PLANET_SYMBOLS,
    ASPECT_SYMBOLS,
    get_zodiac_sign,
    longitude_to_zodiacal,
)
from visualization.styles import (
    LIGHT_SCHEME,
    TECHNICAL_SCHEME,
    get_element_color,
    get_planet_color,
    get_aspect_color,
    LINE_WIDTHS,
)


class ChartWheel:
    """
    Generate natal chart wheel visualizations.

    Creates a traditional circular chart showing planets in signs
    and houses, with optional aspect lines.
    """

    def __init__(
        self,
        style: str = "technical",
        figsize: tuple = (10, 10),
        dpi: int = 300,
    ):
        """
        Initialize chart wheel.

        Args:
            style: Visual style ('technical', 'traditional', 'minimal')
            figsize: Figure size in inches
            dpi: Resolution
        """
        self.style = style
        self.figsize = figsize
        self.dpi = dpi

        if style == "technical":
            self.colors = TECHNICAL_SCHEME
        else:
            self.colors = LIGHT_SCHEME

    def create_wheel(
        self,
        positions: dict,
        houses: dict,
        aspects: Optional[list] = None,
        show_aspects: bool = True,
        show_degrees: bool = True,
        show_minutes: bool = True,
        title: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create a natal chart wheel.

        Args:
            positions: Dictionary of body -> position data
            houses: House data dictionary with cusps
            aspects: List of AspectResult objects
            show_aspects: Whether to draw aspect lines
            show_degrees: Whether to show degree numbers
            show_minutes: Whether to show arc minutes
            title: Chart title

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        ax.set_aspect("equal")
        ax.axis("off")

        # Set limits
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)

        # Draw components from outside to inside
        self._draw_zodiac_ring(ax)
        self._draw_house_cusps(ax, houses)
        self._draw_planets(ax, positions, houses, show_degrees, show_minutes)

        if show_aspects and aspects:
            self._draw_aspects(ax, positions, aspects)

        # Add title
        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        plt.tight_layout()
        return fig

    def _draw_zodiac_ring(self, ax):
        """Draw the outer zodiac sign ring."""
        # Outer circle
        outer_circle = Circle(
            (0, 0),
            1.0,
            fill=False,
            edgecolor=self.colors.text_primary,
            linewidth=LINE_WIDTHS["wheel_border"],
        )
        ax.add_patch(outer_circle)

        # Inner circle (planet zone boundary)
        inner_circle = Circle(
            (0, 0),
            0.85,
            fill=False,
            edgecolor=self.colors.grid,
            linewidth=LINE_WIDTHS["sign_boundary"],
        )
        ax.add_patch(inner_circle)

        # Draw sign divisions and symbols
        for i, sign in enumerate(ZODIAC_SIGNS):
            # Calculate angle (0° Aries at 9 o'clock, moving counter-clockwise)
            start_angle = 180 - (i * 30)
            end_angle = 180 - ((i + 1) * 30)

            # Draw sign boundary line
            angle_rad = np.radians(start_angle)
            ax.plot(
                [0.85 * np.cos(angle_rad), 1.0 * np.cos(angle_rad)],
                [0.85 * np.sin(angle_rad), 1.0 * np.sin(angle_rad)],
                color=self.colors.grid,
                linewidth=LINE_WIDTHS["sign_boundary"],
            )

            # Draw colored arc for sign
            mid_angle = (start_angle + end_angle) / 2
            color = get_element_color(sign, self.colors)

            # Add sign symbol at middle of arc
            symbol_r = 0.92
            symbol_angle = np.radians(mid_angle)
            symbol = ZODIAC_SYMBOLS.get(sign, sign[:3])

            ax.text(
                symbol_r * np.cos(symbol_angle),
                symbol_r * np.sin(symbol_angle),
                symbol,
                ha="center",
                va="center",
                fontsize=12,
                color=color,
            )

    def _draw_house_cusps(self, ax, houses: dict):
        """Draw house cusp lines."""
        cusps = houses.get("cusps", houses.get("houses", {}).get("cusps", []))

        if not cusps:
            return

        for i, cusp in enumerate(cusps):
            # Convert longitude to visual angle
            angle = 180 - cusp

            angle_rad = np.radians(angle)

            # Draw cusp line from center to inner circle
            line_start = 0.3 if i in [0, 3, 6, 9] else 0.5  # Angular houses longer
            line_end = 0.85

            ax.plot(
                [line_start * np.cos(angle_rad), line_end * np.cos(angle_rad)],
                [line_start * np.sin(angle_rad), line_end * np.sin(angle_rad)],
                color=self.colors.text_secondary,
                linewidth=LINE_WIDTHS["house_cusp"],
                linestyle="--" if i not in [0, 3, 6, 9] else "-",
            )

            # Add house number
            num_r = 0.75
            # Offset for readability
            offset_angle = angle - 15
            ax.text(
                num_r * np.cos(np.radians(offset_angle)),
                num_r * np.sin(np.radians(offset_angle)),
                str(i + 1),
                ha="center",
                va="center",
                fontsize=8,
                color=self.colors.text_secondary,
            )

    def _draw_planets(
        self,
        ax,
        positions: dict,
        houses: dict,
        show_degrees: bool,
        show_minutes: bool,
    ):
        """Draw planet symbols and positions."""
        # Calculate planet positions, avoiding overlaps
        planet_angles = {}

        for body, pos in positions.items():
            if hasattr(pos, "longitude_decimal"):
                lon = pos.longitude_decimal
            else:
                lon = pos.get("longitude_decimal", pos.get("longitude", 0))

            # Convert to visual angle
            angle = 180 - lon
            planet_angles[body] = angle

        # Separate overlapping planets
        planet_angles = self._separate_overlaps(planet_angles, min_sep=8)

        # Draw each planet
        for body, angle in planet_angles.items():
            pos = positions[body]

            if hasattr(pos, "longitude_decimal"):
                lon = pos.longitude_decimal
                is_retro = pos.is_retrograde
            else:
                lon = pos.get("longitude_decimal", pos.get("longitude", 0))
                is_retro = pos.get("is_retrograde", False)

            angle_rad = np.radians(angle)
            color = get_planet_color(body, self.colors)

            # Planet symbol position (outer ring)
            symbol_r = 0.65
            symbol = PLANET_SYMBOLS.get(body, body[:2].capitalize())

            ax.text(
                symbol_r * np.cos(angle_rad),
                symbol_r * np.sin(angle_rad),
                symbol,
                ha="center",
                va="center",
                fontsize=14,
                color=color,
                fontweight="bold",
            )

            # Add retrograde indicator
            if is_retro:
                retro_r = 0.58
                ax.text(
                    retro_r * np.cos(angle_rad),
                    retro_r * np.sin(angle_rad),
                    "R",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color=color,
                )

            # Add degree label
            if show_degrees:
                degree_r = 0.52
                sign = get_zodiac_sign(lon)
                degree_in_sign = int(lon % 30)
                minute = int((lon % 1) * 60)

                if show_minutes:
                    label = f"{degree_in_sign}°{minute:02d}'"
                else:
                    label = f"{degree_in_sign}°"

                ax.text(
                    degree_r * np.cos(angle_rad),
                    degree_r * np.sin(angle_rad),
                    label,
                    ha="center",
                    va="center",
                    fontsize=6,
                    color=self.colors.text_secondary,
                    fontfamily="monospace",
                )

    def _draw_aspects(self, ax, positions: dict, aspects: list):
        """Draw aspect lines between planets."""
        for aspect in aspects:
            body1 = aspect.body1 if hasattr(aspect, "body1") else aspect.get("body1")
            body2 = aspect.body2 if hasattr(aspect, "body2") else aspect.get("body2")
            aspect_name = (
                aspect.aspect_name
                if hasattr(aspect, "aspect_name")
                else aspect.get("aspect_name")
            )
            orb = aspect.orb if hasattr(aspect, "orb") else aspect.get("orb", 0)

            if body1 not in positions or body2 not in positions:
                continue

            # Get positions
            pos1 = positions[body1]
            pos2 = positions[body2]

            if hasattr(pos1, "longitude_decimal"):
                lon1 = pos1.longitude_decimal
            else:
                lon1 = pos1.get("longitude_decimal", pos1.get("longitude", 0))

            if hasattr(pos2, "longitude_decimal"):
                lon2 = pos2.longitude_decimal
            else:
                lon2 = pos2.get("longitude_decimal", pos2.get("longitude", 0))

            # Convert to visual angles
            angle1 = np.radians(180 - lon1)
            angle2 = np.radians(180 - lon2)

            # Line endpoints (in center area)
            r = 0.4
            x1, y1 = r * np.cos(angle1), r * np.sin(angle1)
            x2, y2 = r * np.cos(angle2), r * np.sin(angle2)

            # Get aspect color and style
            color = get_aspect_color(aspect_name, self.colors)

            # Line width based on orb (tighter = thicker)
            max_orb = 8.0
            width = LINE_WIDTHS["aspect_major"] * (1 - orb / max_orb)
            width = max(0.5, width)

            # Line style based on aspect type
            if aspect_name in ["conjunction", "opposition", "square"]:
                linestyle = "-"
            elif aspect_name in ["trine", "sextile"]:
                linestyle = "-"
            else:
                linestyle = ":"

            ax.plot(
                [x1, x2],
                [y1, y2],
                color=color,
                linewidth=width,
                linestyle=linestyle,
                alpha=0.7,
            )

    def _separate_overlaps(self, angles: dict, min_sep: float = 8) -> dict:
        """
        Separate overlapping planet positions for visual clarity.

        Args:
            angles: Dictionary of body -> visual angle
            min_sep: Minimum separation in degrees

        Returns:
            Adjusted angles dictionary
        """
        sorted_bodies = sorted(angles.keys(), key=lambda b: angles[b])
        adjusted = angles.copy()

        for i in range(len(sorted_bodies) - 1):
            body1 = sorted_bodies[i]
            body2 = sorted_bodies[i + 1]

            diff = adjusted[body2] - adjusted[body1]

            if diff < min_sep:
                # Push apart
                offset = (min_sep - diff) / 2
                adjusted[body1] -= offset
                adjusted[body2] += offset

        return adjusted


def natal_wheel(
    positions: dict,
    houses: dict,
    aspects: Optional[list] = None,
    style: str = "technical",
    show_aspects: bool = True,
    show_degrees: bool = True,
    show_minutes: bool = True,
    dpi: int = 300,
    title: Optional[str] = None,
) -> plt.Figure:
    """
    Create a natal chart wheel visualization.

    Args:
        positions: Dictionary of body -> position data
        houses: House data dictionary
        aspects: List of AspectResult objects
        style: Visual style
        show_aspects: Whether to show aspect lines
        show_degrees: Whether to show degree numbers
        show_minutes: Whether to show arc minutes
        dpi: Resolution
        title: Chart title

    Returns:
        matplotlib Figure
    """
    wheel = ChartWheel(style=style, dpi=dpi)
    return wheel.create_wheel(
        positions,
        houses,
        aspects,
        show_aspects,
        show_degrees,
        show_minutes,
        title,
    )
