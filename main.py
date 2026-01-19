#!/usr/bin/env python3
"""
Astro Engineering - Main CLI Application

High-precision astronomical calculations for astrological engineering.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.time_engine import TimeEngine, local_to_ut
from core.ephemeris import EphemerisEngine, get_all_positions
from core.houses import calculate_houses, compare_house_systems
from core.aspects import find_all_aspects, aspect_matrix, calculate_aspect_summary
from core.transits import TransitFinder, find_all_transits
from core.stations import find_all_stations
from core.ingress import find_all_ingresses
from reports.generator import ReportGenerator
from data.symbols import longitude_to_zodiacal, format_latitude, format_longitude_geo

console = Console()


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise click.Abort()

    with open(path, "r") as f:
        return yaml.safe_load(f)


def calculate_natal_chart(config: dict) -> dict:
    """
    Calculate complete natal chart from configuration.

    Returns dictionary with all chart data.
    """
    birth = config.get("birth_data", {})

    # Parse birth data
    date_str = birth.get("date", "1986-12-05")
    time_str = birth.get("time", "08:03:00")
    location = birth.get("location", {})
    lat = location.get("latitude", -33.4489)
    lon = location.get("longitude", -70.6693)
    tz = birth.get("timezone", "America/Santiago")

    # Parse datetime
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

    # Time conversion
    time_engine = TimeEngine()
    time_result = time_engine.local_to_ut(dt, tz, lat, lon)

    # Planetary positions
    ephemeris = EphemerisEngine()
    positions = ephemeris.get_all_positions(time_result.jd_tt)

    # House calculation
    house_system = config.get("analysis", {}).get("house_system", "P")
    houses = calculate_houses(time_result.jd_ut, lat, lon, house_system)

    # Add Ascendant and MC to positions for aspect calculation
    positions_with_angles = dict(positions)
    positions_with_angles["ascendant"] = {"longitude_decimal": houses.ascendant}
    positions_with_angles["mc"] = {"longitude_decimal": houses.mc}

    # Aspects
    aspects = find_all_aspects(positions_with_angles, time_result.jd_tt)

    return {
        "birth_data": birth,
        "time_data": time_result.to_dict(),
        "positions": positions,
        "houses": houses.to_dict(),
        "aspects": aspects,
        "calculation_method": ephemeris.calculation_method,
    }


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Astro Engineering - Precision Astrological Calculations

    A scientific approach to astrological analysis using high-precision
    astronomical calculations.
    """
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config/user_case.yaml",
    help="Path to configuration YAML file",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path (markdown)",
)
@click.option(
    "--json",
    "json_output",
    default=None,
    help="Output JSON file path",
)
def natal(config: str, output: Optional[str], json_output: Optional[str]):
    """
    Calculate and display natal chart.

    Uses birth data from configuration file to calculate planetary
    positions, house cusps, and aspects.
    """
    console.print(Panel.fit(
        "[bold blue]ASTRO ENGINEERING - NATAL CHART CALCULATION[/bold blue]",
        border_style="blue",
    ))

    # Load config
    cfg = load_config(config)
    birth = cfg.get("birth_data", {})

    console.print()
    console.print("[bold]INPUT[/bold]")
    console.print("-" * 5)
    console.print(f"Date local:      {birth.get('date')} {birth.get('time')}")
    console.print(f"Timezone:        {birth.get('timezone')}")

    location = birth.get("location", {})
    lat = location.get("latitude", 0)
    lon = location.get("longitude", 0)
    console.print(
        f"Coordinates:     {format_latitude(lat)}, {format_longitude_geo(lon)}, "
        f"{location.get('elevation_m', 0)}m"
    )
    console.print()

    # Calculate chart
    with console.status("[bold green]Calculating chart...[/bold green]"):
        chart = calculate_natal_chart(cfg)

    # Display time conversion
    time_data = chart["time_data"]
    console.print("[bold]TIME CONVERSION[/bold]")
    console.print("-" * 15)
    console.print(f"UTC:             {time_data.get('utc', 'N/A')}")
    console.print(f"Julian Day (UT): {time_data.get('jd_ut', 0):.6f}")
    console.print(f"Julian Day (TT): {time_data.get('jd_tt', 0):.6f}")
    console.print(f"Delta-T:         {time_data.get('delta_t_seconds', 0):.1f} seconds")
    console.print()

    # Display positions table
    console.print("[bold]PLANETARY POSITIONS (Tropical, Geocentric)[/bold]")
    console.print("-" * 46)

    pos_table = Table(show_header=True, header_style="bold")
    pos_table.add_column("Body", width=12)
    pos_table.add_column("Longitude", width=16)
    pos_table.add_column("Lat", width=7)
    pos_table.add_column("Dist AU", width=8)
    pos_table.add_column("Vel °/d", width=8)
    pos_table.add_column("House", width=5)

    houses = chart["houses"]
    house_cusps = houses.get("cusps", [])

    for body, pos in chart["positions"].items():
        if hasattr(pos, "to_dict"):
            pos = pos.to_dict()

        lon = pos.get("longitude_decimal", 0)
        lat_val = pos.get("latitude_decimal", 0)
        dist = pos.get("distance_au", 0)
        speed = pos.get("speed_longitude", 0)
        is_retro = pos.get("is_retrograde", False)
        zodiac = longitude_to_zodiacal(lon, include_seconds=False)

        # Determine house
        house_num = "-"
        if house_cusps:
            for i in range(12):
                start = house_cusps[i]
                end = house_cusps[(i + 1) % 12]
                if start > end:
                    if lon >= start or lon < end:
                        house_num = str(i + 1)
                        break
                else:
                    if start <= lon < end:
                        house_num = str(i + 1)
                        break

        retro_mark = " R" if is_retro else ""
        pos_table.add_row(
            body.capitalize(),
            zodiac[:16],
            f"{lat_val:+.2f}°",
            f"{dist:.4f}",
            f"{speed:+.3f}{retro_mark}",
            house_num,
        )

    console.print(pos_table)
    console.print()

    # Display house cusps
    console.print(f"[bold]HOUSE CUSPS ({houses.get('system_name', 'Unknown')})[/bold]")
    console.print("-" * 20)

    house_table = Table(show_header=True, header_style="bold")
    house_table.add_column("House", width=6)
    house_table.add_column("Cusp", width=18)
    house_table.add_column("Sign", width=12)

    cusps_zodiacal = houses.get("cusps_zodiacal", [])
    for i, cusp in enumerate(house_cusps):
        zodiac = cusps_zodiacal[i] if i < len(cusps_zodiacal) else longitude_to_zodiacal(cusp)
        sign = zodiac.split()[-1] if " " in zodiac else ""
        house_table.add_row(
            str(i + 1),
            f"{cusp:.2f}°",
            zodiac[:20],
        )

    console.print(house_table)
    console.print()

    # Display key angles
    console.print("[bold]KEY ANGLES[/bold]")
    console.print("-" * 10)
    console.print(f"Ascendant:  {longitude_to_zodiacal(houses.get('ascendant', 0))}")
    console.print(f"MC:         {longitude_to_zodiacal(houses.get('mc', 0))}")
    console.print()

    # Display aspects
    aspects = chart.get("aspects", [])
    if aspects:
        console.print(f"[bold]ASPECTS ({len(aspects)} found)[/bold]")
        console.print("-" * 20)

        asp_table = Table(show_header=True, header_style="bold")
        asp_table.add_column("Aspect", width=14)
        asp_table.add_column("Body 1", width=10)
        asp_table.add_column("Body 2", width=10)
        asp_table.add_column("Orb", width=8)
        asp_table.add_column("State", width=10)

        # Sort by orb (tightest first)
        sorted_aspects = sorted(aspects, key=lambda a: a.orb if hasattr(a, "orb") else a.get("orb", 10))

        for asp in sorted_aspects[:20]:  # Show top 20
            if hasattr(asp, "to_dict"):
                asp = asp.to_dict()

            name = asp.get("aspect_name", "N/A").capitalize()
            body1 = asp.get("body1", "").capitalize()
            body2 = asp.get("body2", "").capitalize()
            orb = asp.get("orb", 0)
            state = "Applying" if asp.get("is_applying", False) else "Separating"

            asp_table.add_row(name, body1, body2, f"{orb:.2f}°", state)

        console.print(asp_table)
        console.print()

    # Calculation info
    console.print(f"[dim]Calculation method: {chart.get('calculation_method', 'Unknown')}[/dim]")
    console.print()

    # Generate report if output requested
    if output:
        generator = ReportGenerator()
        report = generator.natal_report(chart, format="markdown")
        Path(output).write_text(report)
        console.print(f"[green]Report saved to: {output}[/green]")

    if json_output:
        generator = ReportGenerator()
        generator.export_json(chart, filepath=json_output)
        console.print(f"[green]JSON exported to: {json_output}[/green]")


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config/user_case.yaml",
    help="Path to configuration YAML file",
)
@click.option(
    "--start",
    default=None,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end",
    default=None,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--body",
    "-b",
    multiple=True,
    help="Transiting bodies to track (can specify multiple)",
)
def transits(config: str, start: Optional[str], end: Optional[str], body: tuple):
    """
    Calculate transits to natal chart.

    Finds exact times when transiting planets form aspects to
    natal positions.
    """
    console.print(Panel.fit(
        "[bold blue]ASTRO ENGINEERING - TRANSIT ANALYSIS[/bold blue]",
        border_style="blue",
    ))

    # Load config and calculate natal chart
    cfg = load_config(config)

    with console.status("[bold green]Calculating natal chart...[/bold green]"):
        chart = calculate_natal_chart(cfg)

    # Get natal positions
    natal_positions = {}
    for body_name, pos in chart["positions"].items():
        if hasattr(pos, "longitude_decimal"):
            natal_positions[body_name] = pos.longitude_decimal
        else:
            natal_positions[body_name] = pos.get("longitude_decimal", 0)

    # Add angles
    houses = chart["houses"]
    natal_positions["ascendant"] = houses.get("ascendant", 0)
    natal_positions["mc"] = houses.get("mc", 0)

    # Date range
    analysis = cfg.get("analysis", {}).get("transit_range", {})
    start_date = datetime.strptime(
        start or analysis.get("start", "2024-01-01"), "%Y-%m-%d"
    )
    end_date = datetime.strptime(
        end or analysis.get("end", "2024-12-31"), "%Y-%m-%d"
    )

    # Bodies to track
    bodies = list(body) if body else ["jupiter", "saturn", "uranus", "neptune", "pluto"]

    console.print()
    console.print(f"[bold]TRANSIT SEARCH[/bold]")
    console.print("-" * 14)
    console.print(f"Period:   {start_date.date()} to {end_date.date()}")
    console.print(f"Bodies:   {', '.join(bodies)}")
    console.print()

    with console.status("[bold green]Finding transits...[/bold green]"):
        transits_df = find_all_transits(
            natal_positions,
            start_date,
            end_date,
            transiting_bodies=bodies,
        )

    if transits_df.empty:
        console.print("[yellow]No transits found in date range.[/yellow]")
        return

    console.print(f"[green]Found {len(transits_df)} transit events[/green]")
    console.print()

    # Display transit table
    transit_table = Table(show_header=True, header_style="bold")
    transit_table.add_column("Date", width=12)
    transit_table.add_column("Transit", width=10)
    transit_table.add_column("Aspect", width=12)
    transit_table.add_column("Natal", width=10)
    transit_table.add_column("R", width=3)

    for _, row in transits_df.head(30).iterrows():
        dt = row.get("datetime_utc")
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", ""))
        date_str = dt.strftime("%Y-%m-%d")

        transit_body = row.get("transiting_body", "?").capitalize()
        aspect = row.get("aspect", "?").capitalize()
        natal_point = row.get("natal_point", "?").capitalize()
        is_retro = "R" if row.get("is_retrograde", False) else ""

        transit_table.add_row(date_str, transit_body, aspect, natal_point, is_retro)

    console.print(transit_table)

    if len(transits_df) > 30:
        console.print(f"[dim]... and {len(transits_df) - 30} more transits[/dim]")


@cli.command()
@click.option(
    "--start",
    default=None,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end",
    default=None,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--body",
    "-b",
    multiple=True,
    help="Bodies to track (can specify multiple)",
)
def stations(start: Optional[str], end: Optional[str], body: tuple):
    """
    Find planetary stations (retrograde/direct).

    Lists dates when planets station retrograde or direct.
    """
    console.print(Panel.fit(
        "[bold blue]ASTRO ENGINEERING - PLANETARY STATIONS[/bold blue]",
        border_style="blue",
    ))

    # Date range
    start_date = datetime.strptime(start or "2024-01-01", "%Y-%m-%d")
    end_date = datetime.strptime(end or "2024-12-31", "%Y-%m-%d")
    bodies = list(body) if body else None

    console.print()
    console.print(f"[bold]STATION SEARCH[/bold]")
    console.print(f"Period: {start_date.date()} to {end_date.date()}")
    console.print()

    with console.status("[bold green]Finding stations...[/bold green]"):
        station_events = find_all_stations(start_date, end_date, bodies)

    if not station_events:
        console.print("[yellow]No stations found in date range.[/yellow]")
        return

    console.print(f"[green]Found {len(station_events)} station events[/green]")
    console.print()

    station_table = Table(show_header=True, header_style="bold")
    station_table.add_column("Date", width=12)
    station_table.add_column("Time", width=8)
    station_table.add_column("Body", width=10)
    station_table.add_column("Type", width=12)
    station_table.add_column("Position", width=20)

    for event in station_events:
        date_str = event.datetime_utc.strftime("%Y-%m-%d")
        time_str = event.datetime_utc.strftime("%H:%M")
        station_type = event.station_type.capitalize()

        station_table.add_row(
            date_str,
            time_str,
            event.body.capitalize(),
            station_type,
            event.longitude_zodiacal[:20],
        )

    console.print(station_table)


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config/user_case.yaml",
    help="Path to configuration YAML file",
)
@click.option(
    "--systems",
    "-s",
    default="P,K,E,W",
    help="House systems to compare (comma-separated)",
)
def compare_houses(config: str, systems: str):
    """
    Compare different house systems.

    Shows how house cusps differ between various calculation methods.
    """
    console.print(Panel.fit(
        "[bold blue]ASTRO ENGINEERING - HOUSE SYSTEM COMPARISON[/bold blue]",
        border_style="blue",
    ))

    # Load config
    cfg = load_config(config)
    birth = cfg.get("birth_data", {})

    # Parse birth data
    date_str = birth.get("date", "1986-12-05")
    time_str = birth.get("time", "08:03:00")
    location = birth.get("location", {})
    lat = location.get("latitude", -33.4489)
    lon = location.get("longitude", -70.6693)
    tz = birth.get("timezone", "America/Santiago")

    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    time_result = local_to_ut(dt, tz, lat, lon)

    system_list = [s.strip() for s in systems.split(",")]

    console.print()
    with console.status("[bold green]Comparing house systems...[/bold green]"):
        df = compare_house_systems(time_result.jd_ut, lat, lon, system_list)

    console.print(df.to_string())


@cli.command()
def version():
    """Show version and calculation method information."""
    console.print(Panel.fit(
        "[bold blue]ASTRO ENGINEERING[/bold blue]\n"
        "Version 1.0.0\n\n"
        "High-precision astronomical calculations\n"
        "for astrological engineering analysis.",
        border_style="blue",
    ))

    ephemeris = EphemerisEngine()
    console.print()
    console.print(f"Ephemeris method: {ephemeris.calculation_method}")
    if ephemeris.ephemeris_path:
        console.print(f"Ephemeris path: {ephemeris.ephemeris_path}")


if __name__ == "__main__":
    cli()
