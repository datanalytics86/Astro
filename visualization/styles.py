"""
Styles Module - Color schemes and styling for visualizations.

Provides consistent styling across all visualization modules.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ColorScheme:
    """Color scheme for astrological visualizations."""

    # Sign element colors
    fire: str = "#E74C3C"
    earth: str = "#27AE60"
    air: str = "#3498DB"
    water: str = "#9B59B6"

    # Aspect colors
    conjunction: str = "#FFD700"
    opposition: str = "#E74C3C"
    trine: str = "#27AE60"
    square: str = "#E74C3C"
    sextile: str = "#3498DB"
    quincunx: str = "#95A5A6"
    minor: str = "#BDC3C7"

    # Planet colors
    sun: str = "#F1C40F"
    moon: str = "#BDC3C7"
    mercury: str = "#9B59B6"
    venus: str = "#27AE60"
    mars: str = "#E74C3C"
    jupiter: str = "#E67E22"
    saturn: str = "#7F8C8D"
    uranus: str = "#1ABC9C"
    neptune: str = "#3498DB"
    pluto: str = "#2C3E50"

    # Background colors
    background: str = "#FFFFFF"
    wheel_background: str = "#F5F5F5"
    grid: str = "#CCCCCC"

    # Text colors
    text_primary: str = "#2C3E50"
    text_secondary: str = "#7F8C8D"


# Default color schemes
LIGHT_SCHEME = ColorScheme()

DARK_SCHEME = ColorScheme(
    background="#1A1A2E",
    wheel_background="#16213E",
    grid="#3A3A5A",
    text_primary="#FFFFFF",
    text_secondary="#A0A0B0",
)

# Technical scheme (high contrast, monochrome-friendly)
TECHNICAL_SCHEME = ColorScheme(
    fire="#D32F2F",
    earth="#388E3C",
    air="#1976D2",
    water="#7B1FA2",
    background="#FFFFFF",
    wheel_background="#FAFAFA",
    text_primary="#000000",
    text_secondary="#666666",
)


def get_element_color(sign: str, scheme: ColorScheme = LIGHT_SCHEME) -> str:
    """Get color for a zodiac sign based on its element."""
    elements = {
        "Aries": "fire",
        "Taurus": "earth",
        "Gemini": "air",
        "Cancer": "water",
        "Leo": "fire",
        "Virgo": "earth",
        "Libra": "air",
        "Scorpio": "water",
        "Sagittarius": "fire",
        "Capricorn": "earth",
        "Aquarius": "air",
        "Pisces": "water",
    }

    element = elements.get(sign, "earth")
    return getattr(scheme, element, scheme.earth)


def get_planet_color(planet: str, scheme: ColorScheme = LIGHT_SCHEME) -> str:
    """Get color for a planet."""
    return getattr(scheme, planet.lower(), scheme.text_primary)


def get_aspect_color(aspect: str, scheme: ColorScheme = LIGHT_SCHEME) -> str:
    """Get color for an aspect type."""
    return getattr(scheme, aspect.lower(), scheme.minor)


# Line widths
LINE_WIDTHS = {
    "aspect_major": 1.5,
    "aspect_minor": 0.75,
    "house_cusp": 1.0,
    "sign_boundary": 0.5,
    "wheel_border": 2.0,
}

# Font settings
FONTS = {
    "title": {"family": "sans-serif", "size": 16, "weight": "bold"},
    "label": {"family": "sans-serif", "size": 10, "weight": "normal"},
    "degree": {"family": "monospace", "size": 8, "weight": "normal"},
    "symbol": {"family": "sans-serif", "size": 12, "weight": "normal"},
}
