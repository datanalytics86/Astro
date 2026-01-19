"""
Report Generator Module - Generate formatted reports.

Creates markdown, JSON, and iCal format reports for natal charts
and transit analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from icalendar import Calendar, Event

from data.symbols import (
    ZODIAC_SYMBOLS,
    PLANET_SYMBOLS,
    ASPECT_SYMBOLS,
    longitude_to_zodiacal,
    format_latitude,
    format_longitude_geo,
)


class ReportGenerator:
    """
    Generate formatted reports for astrological data.

    Supports multiple output formats including Markdown, JSON, and iCal.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def natal_report(
        self,
        chart: dict,
        format: str = "markdown",
        include_aspects: bool = True,
    ) -> str:
        """
        Generate a natal chart report.

        Args:
            chart: Dictionary containing:
                - birth_data: date, time, location info
                - time_data: TimeResult data
                - positions: planetary positions
                - houses: house data
                - aspects: aspect list
            format: Output format ('markdown' or 'text')
            include_aspects: Whether to include aspect list

        Returns:
            Formatted report string
        """
        if format == "markdown":
            return self._natal_report_markdown(chart, include_aspects)
        else:
            return self._natal_report_text(chart, include_aspects)

    def _natal_report_markdown(self, chart: dict, include_aspects: bool) -> str:
        """Generate markdown natal report."""
        lines = []

        # Header
        lines.append("# NATAL CHART - ASTROLOGICAL ENGINEERING ANALYSIS")
        lines.append("")

        # Birth data section
        birth = chart.get("birth_data", {})
        time_data = chart.get("time_data", {})

        lines.append("## Input Data")
        lines.append("")
        lines.append(f"- **Date**: {birth.get('date', 'N/A')}")
        lines.append(f"- **Time**: {birth.get('time', 'N/A')}")
        lines.append(f"- **Location**: {birth.get('location', {}).get('name', 'N/A')}")

        lat = birth.get("location", {}).get("latitude", 0)
        lon = birth.get("location", {}).get("longitude", 0)
        elev = birth.get("location", {}).get("elevation_m", 0)

        lines.append(f"- **Coordinates**: {format_latitude(lat)}, {format_longitude_geo(lon)}")
        lines.append(f"- **Elevation**: {elev}m")
        lines.append(f"- **Timezone**: {birth.get('timezone', 'N/A')}")
        lines.append("")

        # Time conversion section
        lines.append("## Time Conversion")
        lines.append("")
        lines.append(f"- **UTC**: {time_data.get('utc', 'N/A')}")
        lines.append(f"- **Julian Day (UT)**: {time_data.get('jd_ut', 0):.6f}")
        lines.append(f"- **Julian Day (TT)**: {time_data.get('jd_tt', 0):.6f}")
        lines.append(f"- **Delta-T**: {time_data.get('delta_t_seconds', 0):.1f} seconds")
        lines.append(f"- **DST Active**: {time_data.get('dst_active', False)}")
        lines.append("")

        # Planetary positions
        positions = chart.get("positions", {})
        if positions:
            lines.append("## Planetary Positions")
            lines.append("")
            lines.append("| Body | Longitude | Sign | Speed | Retro | House |")
            lines.append("|------|-----------|------|-------|-------|-------|")

            houses_data = chart.get("houses", {})

            for body, pos in positions.items():
                if hasattr(pos, "to_dict"):
                    pos = pos.to_dict()

                lon_zodiac = pos.get("longitude_zodiacal", "N/A")
                sign = pos.get("zodiac_sign", "N/A")
                speed = pos.get("speed_longitude", 0)
                is_retro = "R" if pos.get("is_retrograde", False) else ""

                # Get house placement
                house = self._get_house_for_position(
                    pos.get("longitude_decimal", 0),
                    houses_data,
                )

                symbol = PLANET_SYMBOLS.get(body, body[:3])
                lines.append(
                    f"| {symbol} {body.capitalize()} | {lon_zodiac[:15]} | "
                    f"{sign} | {speed:+.3f}°/d | {is_retro} | {house} |"
                )

            lines.append("")

        # House cusps
        houses = chart.get("houses", {})
        if houses:
            cusps = houses.get("cusps", [])
            system = houses.get("system_name", houses.get("system", "Unknown"))

            lines.append(f"## House Cusps ({system})")
            lines.append("")
            lines.append("| House | Cusp | Sign |")
            lines.append("|-------|------|------|")

            cusps_zodiac = houses.get("cusps_zodiacal", [])

            for i, cusp in enumerate(cusps):
                zodiac = cusps_zodiac[i] if i < len(cusps_zodiac) else longitude_to_zodiacal(cusp)
                lines.append(f"| {i + 1} | {cusp:.2f}° | {zodiac[:20]} |")

            lines.append("")

            # Key angles
            lines.append("### Key Angles")
            lines.append("")
            asc = houses.get("ascendant", 0)
            mc = houses.get("mc", 0)
            lines.append(f"- **Ascendant**: {longitude_to_zodiacal(asc)}")
            lines.append(f"- **Midheaven (MC)**: {longitude_to_zodiacal(mc)}")
            lines.append("")

        # Aspects
        aspects = chart.get("aspects", [])
        if include_aspects and aspects:
            lines.append("## Aspects")
            lines.append("")
            lines.append("| Aspect | Body 1 | Body 2 | Orb | App/Sep |")
            lines.append("|--------|--------|--------|-----|---------|")

            for asp in aspects:
                if hasattr(asp, "to_dict"):
                    asp = asp.to_dict()

                name = asp.get("aspect_name", "N/A")
                symbol = ASPECT_SYMBOLS.get(name, name[:3])
                body1 = asp.get("body1", "").capitalize()
                body2 = asp.get("body2", "").capitalize()
                orb = asp.get("orb", 0)
                app_sep = "Applying" if asp.get("is_applying", False) else "Separating"

                lines.append(
                    f"| {symbol} {name.capitalize()} | {body1} | {body2} | "
                    f"{orb:.2f}° | {app_sep} |"
                )

            lines.append("")

        # Calculation info
        calc_method = chart.get("calculation_method", "Unknown")
        lines.append("## Calculation Information")
        lines.append("")
        lines.append(f"- **Method**: {calc_method}")
        lines.append(f"- **Generated**: {datetime.now().isoformat()}")
        lines.append("")

        return "\n".join(lines)

    def _natal_report_text(self, chart: dict, include_aspects: bool) -> str:
        """Generate plain text natal report."""
        lines = []
        sep = "=" * 70

        lines.append(sep)
        lines.append(" NATAL CHART - ASTROLOGICAL ENGINEERING CALCULATION")
        lines.append(sep)
        lines.append("")

        # Simplified text version
        birth = chart.get("birth_data", {})
        lines.append(" INPUT")
        lines.append(" " + "-" * 5)
        lines.append(f" Date local:      {birth.get('date', 'N/A')} {birth.get('time', '')}")
        lines.append(f" Timezone:        {birth.get('timezone', 'N/A')}")
        lines.append("")

        # Positions
        positions = chart.get("positions", {})
        if positions:
            lines.append(" PLANETARY POSITIONS (Tropical, Geocentric)")
            lines.append(" " + "-" * 46)
            lines.append(" Body        | Longitude      | Lat    | Vel    | House")
            lines.append(" " + "-" * 58)

            for body, pos in positions.items():
                if hasattr(pos, "to_dict"):
                    pos = pos.to_dict()

                lon = pos.get("longitude_decimal", 0)
                lat = pos.get("latitude_decimal", 0)
                speed = pos.get("speed_longitude", 0)
                zodiac = longitude_to_zodiacal(lon, include_seconds=False)

                lines.append(
                    f" {body.capitalize():<11} | {zodiac:<14} | {lat:+5.1f}° | "
                    f"{speed:+.2f} | -"
                )

            lines.append("")

        lines.append(sep)

        return "\n".join(lines)

    def _get_house_for_position(self, longitude: float, houses: dict) -> str:
        """Determine house for a given longitude."""
        cusps = houses.get("cusps", [])
        if not cusps:
            return "-"

        for i in range(12):
            start = cusps[i]
            end = cusps[(i + 1) % 12]

            # Handle wrap-around
            if start > end:
                if longitude >= start or longitude < end:
                    return str(i + 1)
            else:
                if start <= longitude < end:
                    return str(i + 1)

        return "12"

    def transit_report(
        self,
        transits_df: pd.DataFrame,
        year: int,
        natal_chart: Optional[dict] = None,
        format: str = "markdown",
    ) -> str:
        """
        Generate a transit report for a year.

        Args:
            transits_df: DataFrame from TransitFinder
            year: Year for the report
            natal_chart: Optional natal chart for context
            format: Output format

        Returns:
            Formatted report string
        """
        lines = []

        lines.append(f"# Transit Report - {year}")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().isoformat()}*")
        lines.append("")

        if transits_df.empty:
            lines.append("No transits found for this period.")
            return "\n".join(lines)

        # Filter to year
        df = transits_df.copy()
        if "datetime_utc" in df.columns:
            if df["datetime_utc"].dtype == object:
                df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])
            df = df[df["datetime_utc"].dt.year == year]

        if df.empty:
            lines.append(f"No transits found for {year}.")
            return "\n".join(lines)

        # Group by month
        df["month"] = df["datetime_utc"].dt.month
        df["month_name"] = df["datetime_utc"].dt.strftime("%B")

        for month in range(1, 13):
            month_df = df[df["month"] == month]
            if month_df.empty:
                continue

            month_name = month_df.iloc[0]["month_name"]
            lines.append(f"## {month_name} {year}")
            lines.append("")

            for _, row in month_df.iterrows():
                dt = row["datetime_utc"]
                body = row.get("transiting_body", "?").capitalize()
                aspect = row.get("aspect", "?")
                natal = row.get("natal_point", "?").capitalize()
                is_retro = " (R)" if row.get("is_retrograde", False) else ""

                symbol = ASPECT_SYMBOLS.get(aspect, aspect[:3])
                date_str = dt.strftime("%Y-%m-%d %H:%M")

                lines.append(f"- **{date_str}**: {body}{is_retro} {symbol} {aspect} natal {natal}")

            lines.append("")

        return "\n".join(lines)

    def export_json(
        self,
        chart: dict,
        transits: Optional[pd.DataFrame] = None,
        filepath: Optional[str] = None,
    ) -> str:
        """
        Export all data to JSON.

        Args:
            chart: Natal chart data
            transits: Optional transits DataFrame
            filepath: Output file path (or return string if None)

        Returns:
            JSON string
        """
        data = {"chart": self._prepare_for_json(chart)}

        if transits is not None and not transits.empty:
            data["transits"] = transits.to_dict(orient="records")

        data["metadata"] = {
            "generated": datetime.now().isoformat(),
            "version": "1.0",
        }

        json_str = json.dumps(data, indent=2, default=str)

        if filepath:
            path = Path(filepath)
            path.write_text(json_str)

        return json_str

    def _prepare_for_json(self, obj):
        """Convert objects for JSON serialization."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        else:
            return obj

    def export_ical(
        self,
        transits_df: pd.DataFrame,
        filepath: str,
        title_prefix: str = "Transit",
    ) -> None:
        """
        Export transits to iCal format.

        Args:
            transits_df: Transit events DataFrame
            filepath: Output .ics file path
            title_prefix: Prefix for event titles
        """
        cal = Calendar()
        cal.add("prodid", "-//Astro Engineering//Transit Calendar//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")

        for _, row in transits_df.iterrows():
            event = Event()

            # Parse datetime
            dt = row.get("datetime_utc")
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

            body = row.get("transiting_body", "Planet").capitalize()
            aspect = row.get("aspect", "aspect")
            natal = row.get("natal_point", "point").capitalize()
            is_retro = " (R)" if row.get("is_retrograde", False) else ""

            title = f"{title_prefix}: {body}{is_retro} {aspect} {natal}"
            event.add("summary", title)
            event.add("dtstart", dt.date())
            event.add("dtend", dt.date())

            description = (
                f"Transiting {body} forms {aspect} to natal {natal}\n"
                f"Retrograde: {row.get('is_retrograde', False)}\n"
                f"Pass: {row.get('pass_number', 1)}"
            )
            event.add("description", description)

            # Add unique ID
            uid = f"{dt.isoformat()}-{body}-{aspect}-{natal}@astro-eng"
            event.add("uid", uid)

            cal.add_component(event)

        path = Path(filepath)
        path.write_bytes(cal.to_ical())


# Module-level instance
_generator = ReportGenerator()


def natal_report(chart: dict, format: str = "markdown") -> str:
    """Generate natal chart report."""
    return _generator.natal_report(chart, format)


def transit_report(transits_df: pd.DataFrame, year: int) -> str:
    """Generate transit report."""
    return _generator.transit_report(transits_df, year)


def export_json(chart: dict, transits=None, filepath=None) -> str:
    """Export to JSON."""
    return _generator.export_json(chart, transits, filepath)


def export_ical(transits_df: pd.DataFrame, filepath: str) -> None:
    """Export to iCal."""
    _generator.export_ical(transits_df, filepath)
