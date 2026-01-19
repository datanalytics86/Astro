"""
Visualization module for astrological engineering.

Provides various visualization tools for natal charts, transits,
and activation patterns.
"""

from .styles import (
    ColorScheme,
    LIGHT_SCHEME,
    DARK_SCHEME,
    TECHNICAL_SCHEME,
    get_element_color,
    get_planet_color,
    get_aspect_color,
    LINE_WIDTHS,
    FONTS,
)

from .wheel import (
    ChartWheel,
    natal_wheel,
)

from .timeline import (
    transit_timeline,
    multi_body_timeline,
    create_transit_gantt,
)

from .heatmap import (
    activation_heatmap,
    calendar_heatmap,
    monthly_summary_heatmap,
)

from .positions import (
    position_plot,
    retrograde_loops,
    aspect_approach_chart,
)

__all__ = [
    # Styles
    "ColorScheme",
    "LIGHT_SCHEME",
    "DARK_SCHEME",
    "TECHNICAL_SCHEME",
    "get_element_color",
    "get_planet_color",
    "get_aspect_color",
    "LINE_WIDTHS",
    "FONTS",
    # Wheel
    "ChartWheel",
    "natal_wheel",
    # Timeline
    "transit_timeline",
    "multi_body_timeline",
    "create_transit_gantt",
    # Heatmap
    "activation_heatmap",
    "calendar_heatmap",
    "monthly_summary_heatmap",
    # Positions
    "position_plot",
    "retrograde_loops",
    "aspect_approach_chart",
]
