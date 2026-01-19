# Astro Engineering

High-precision astronomical calculations for astrological engineering analysis.

## Overview

This project provides a scientific, engineering-focused approach to astrological calculations. It emphasizes:

- **Astronomical Precision**: Calculations verified against sources like JPL Horizons
- **Reproducibility**: All algorithms documented with uncertainty quantification
- **Separation of Data and Interpretation**: Clear distinction between astronomical data and astrological interpretation
- **Standard Output Formats**: JSON, CSV, Markdown for further analysis

## Features

### Core Calculations

- **Time Engine**: Rigorous conversion between time scales (UTC, UT1, TT, TDB)
- **Ephemeris**: High-precision planetary positions using Swiss Ephemeris
- **Houses**: Multiple house systems (Placidus, Koch, Equal, Whole Sign, etc.)
- **Aspects**: Aspect detection with configurable orbs and applying/separating analysis
- **Transits**: High-precision transit finding with retrograde handling
- **Stations**: Planetary station (retrograde/direct) detection
- **Ingress**: Sign change detection

### Visualization

- Natal chart wheels
- Transit timelines (interactive Plotly)
- Activation heatmaps
- Position plots over time

### Reports

- Markdown and text reports
- JSON export
- iCal calendar export for transits

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd astro-engineering

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Download Swiss Ephemeris files for highest precision
# Place .se1 files in data/ephemeris/
```

## Quick Start

### Command Line Interface

```bash
# Calculate natal chart
python main.py natal --config config/user_case.yaml

# Find transits
python main.py transits --config config/user_case.yaml --start 2024-01-01 --end 2024-12-31

# Find planetary stations
python main.py stations --start 2024-01-01 --end 2024-12-31

# Compare house systems
python main.py compare-houses --config config/user_case.yaml
```

### Python API

```python
from datetime import datetime
from core.time_engine import local_to_ut
from core.ephemeris import get_all_positions
from core.houses import calculate_houses
from core.aspects import find_all_aspects

# Convert local time to astronomical time scales
time_result = local_to_ut(
    datetime(1986, 12, 5, 8, 3, 0),
    "America/Santiago",
    lat=-33.4489,
    lon=-70.6693,
)

# Get planetary positions
positions = get_all_positions(time_result.jd_tt)

# Calculate houses
houses = calculate_houses(
    time_result.jd_ut,
    latitude=-33.4489,
    longitude=-70.6693,
    system="P",  # Placidus
)

# Find aspects
aspects = find_all_aspects(positions)

# Print results
for body, pos in positions.items():
    print(f"{body}: {pos.longitude_zodiacal}")
```

## Project Structure

```
astro-engineering/
├── config/
│   ├── default.yaml           # Default configuration
│   └── user_case.yaml         # Case study configuration
├── core/
│   ├── time_engine.py         # Time conversions
│   ├── ephemeris.py           # Planetary positions
│   ├── houses.py              # House systems
│   ├── aspects.py             # Aspect detection
│   ├── transits.py            # Transit finder
│   ├── stations.py            # Station detection
│   ├── ingress.py             # Sign ingress detection
│   └── windows.py             # Activation windows
├── visualization/
│   ├── wheel.py               # Natal wheel charts
│   ├── timeline.py            # Transit timelines
│   ├── heatmap.py             # Activation heatmaps
│   └── positions.py           # Position plots
├── reports/
│   └── generator.py           # Report generation
├── data/
│   ├── symbols.py             # Unicode symbols
│   └── ephemeris/             # Swiss Ephemeris data files
├── tests/
│   └── test_*.py              # Test files
├── main.py                    # CLI application
└── requirements.txt           # Dependencies
```

## Calculation Methods

### Swiss Ephemeris

This project uses the Swiss Ephemeris library for planetary calculations:

- **SWIEPH Mode**: Uses .se1 data files for highest precision (~0.001 arcsec)
- **MOSEPH Mode**: Moshier algorithm fallback (~0.1 arcsec precision)

### Time Scales

- **UTC**: Coordinated Universal Time
- **UT1**: Universal Time (rotation-based)
- **TT**: Terrestrial Time (atomic time scale)
- **TDB**: Barycentric Dynamical Time (for planetary calculations)
- **Delta-T**: Difference between TT and UT1

### House Systems Supported

| Code | System | Description |
|------|--------|-------------|
| P | Placidus | Time-based, most popular |
| K | Koch | Place-based |
| R | Regiomontanus | Medieval rational |
| C | Campanus | Prime vertical |
| E | Equal | 30° from Ascendant |
| W | Whole Sign | Sign-based |
| B | Alcabitius | Semi-arc based |
| M | Morinus | Equatorial |
| T | Topocentric | Polich-Page |

## Case Study

The default configuration includes a case study:

- **Date**: December 5, 1986
- **Time**: 08:03:00 local
- **Location**: Santiago, Chile (-33.4489°, -70.6693°)
- **Timezone**: America/Santiago (UTC-3, summer time)

Expected results for validation:
- Ascendant: ~11° Capricorn
- MC: ~25° Libra
- Sun: ~13° Sagittarius
- Moon: ~6° Aquarius

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ephemeris.py -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

## Precision and Validation

### Precision Estimates

| Calculation | SWIEPH | MOSEPH |
|-------------|--------|--------|
| Planets | ~0.001" | ~0.1" |
| Moon | ~0.01" | ~1" |
| Houses | ~1' | ~1' |

### Validation

Positions can be validated against:
- JPL Horizons: https://ssd.jpl.nasa.gov/horizons/
- Swiss Ephemeris test data
- Published ephemerides

## Dependencies

- **pyswisseph**: Swiss Ephemeris calculations
- **numpy**: Numerical computing
- **pandas**: Data manipulation
- **matplotlib**: Static visualizations
- **plotly**: Interactive visualizations
- **astropy**: Coordinate verification
- **timezonefinder**: Timezone lookup
- **pytz**: Timezone handling
- **click**: CLI framework
- **rich**: Terminal formatting
- **pyyaml**: Configuration files
- **icalendar**: Calendar export

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- All calculations include precision estimates
- New features have tests
- Code follows existing style
