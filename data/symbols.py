"""
Unicode symbols for astrological representation.
Provides both Unicode glyphs and ASCII fallbacks.
"""

# Zodiac sign symbols
ZODIAC_SYMBOLS = {
    "Aries": "\u2648",
    "Taurus": "\u2649",
    "Gemini": "\u264A",
    "Cancer": "\u264B",
    "Leo": "\u264C",
    "Virgo": "\u264D",
    "Libra": "\u264E",
    "Scorpio": "\u264F",
    "Sagittarius": "\u2650",
    "Capricorn": "\u2651",
    "Aquarius": "\u2652",
    "Pisces": "\u2653",
}

# Zodiac abbreviations (3-letter)
ZODIAC_ABBREV = {
    "Aries": "Ari",
    "Taurus": "Tau",
    "Gemini": "Gem",
    "Cancer": "Can",
    "Leo": "Leo",
    "Virgo": "Vir",
    "Libra": "Lib",
    "Scorpio": "Sco",
    "Sagittarius": "Sag",
    "Capricorn": "Cap",
    "Aquarius": "Aqu",
    "Pisces": "Pis",
}

# Zodiac signs in order (0-11)
ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# Planet/body symbols
PLANET_SYMBOLS = {
    "sun": "\u2609",
    "moon": "\u263D",
    "mercury": "\u263F",
    "venus": "\u2640",
    "mars": "\u2642",
    "jupiter": "\u2643",
    "saturn": "\u2644",
    "uranus": "\u2645",
    "neptune": "\u2646",
    "pluto": "\u2647",
    "chiron": "\u26B7",
    "mean_node": "\u260A",  # North Node (ascending)
    "true_node": "\u260A",
    "south_node": "\u260B",  # South Node (descending)
    "mean_apogee": "\u26B8",  # Lilith
    "ascendant": "Asc",
    "mc": "MC",
    "vertex": "Vx",
}

# Planet names for display
PLANET_NAMES = {
    "sun": "Sun",
    "moon": "Moon",
    "mercury": "Mercury",
    "venus": "Venus",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "saturn": "Saturn",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "pluto": "Pluto",
    "chiron": "Chiron",
    "mean_node": "North Node (Mean)",
    "true_node": "North Node (True)",
    "mean_apogee": "Lilith (Mean)",
    "ascendant": "Ascendant",
    "mc": "Midheaven",
    "vertex": "Vertex",
}

# Aspect symbols
ASPECT_SYMBOLS = {
    "conjunction": "\u260C",
    "opposition": "\u260D",
    "trine": "\u25B3",
    "square": "\u25A1",
    "sextile": "\u2736",
    "quincunx": "Qx",
    "semisextile": "\u26BA",
    "semisquare": "\u2220",
    "sesquiquadrate": "\u26BC",
    "quintile": "Q",
    "biquintile": "bQ",
}

# Aspect angles
ASPECT_ANGLES = {
    "conjunction": 0,
    "opposition": 180,
    "trine": 120,
    "square": 90,
    "sextile": 60,
    "quincunx": 150,
    "semisextile": 30,
    "semisquare": 45,
    "sesquiquadrate": 135,
    "quintile": 72,
    "biquintile": 144,
}

# Element associations
ELEMENTS = {
    "Aries": "Fire",
    "Taurus": "Earth",
    "Gemini": "Air",
    "Cancer": "Water",
    "Leo": "Fire",
    "Virgo": "Earth",
    "Libra": "Air",
    "Scorpio": "Water",
    "Sagittarius": "Fire",
    "Capricorn": "Earth",
    "Aquarius": "Air",
    "Pisces": "Water",
}

# Modality associations
MODALITIES = {
    "Aries": "Cardinal",
    "Taurus": "Fixed",
    "Gemini": "Mutable",
    "Cancer": "Cardinal",
    "Leo": "Fixed",
    "Virgo": "Mutable",
    "Libra": "Cardinal",
    "Scorpio": "Fixed",
    "Sagittarius": "Mutable",
    "Capricorn": "Cardinal",
    "Aquarius": "Fixed",
    "Pisces": "Mutable",
}

# Retrograde symbol
RETROGRADE_SYMBOL = "\u211E"  # Rx

# Degree symbols
DEGREE_SYMBOL = "\u00B0"
MINUTE_SYMBOL = "\u2032"
SECOND_SYMBOL = "\u2033"


def get_zodiac_sign(longitude: float) -> str:
    """Get zodiac sign name from ecliptic longitude (0-360)."""
    sign_index = int(longitude / 30) % 12
    return ZODIAC_SIGNS[sign_index]


def get_sign_degree(longitude: float) -> int:
    """Get degree within sign (0-29) from ecliptic longitude."""
    return int(longitude % 30)


def longitude_to_zodiacal(longitude: float, include_seconds: bool = True) -> str:
    """
    Convert ecliptic longitude to zodiacal notation.

    Args:
        longitude: Ecliptic longitude in decimal degrees (0-360)
        include_seconds: Whether to include arc seconds

    Returns:
        String like "15°23'45\" Leo" or "15°23' Leo"
    """
    sign = get_zodiac_sign(longitude)
    degree_in_sign = longitude % 30

    degrees = int(degree_in_sign)
    minutes_float = (degree_in_sign - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    if include_seconds:
        return f"{degrees:02d}{DEGREE_SYMBOL}{minutes:02d}{MINUTE_SYMBOL}{seconds:05.2f}{SECOND_SYMBOL} {sign}"
    else:
        return f"{degrees:02d}{DEGREE_SYMBOL}{minutes:02d}{MINUTE_SYMBOL} {sign}"


def longitude_to_dms(longitude: float) -> str:
    """
    Convert longitude to degrees/minutes/seconds notation.

    Args:
        longitude: Longitude in decimal degrees

    Returns:
        String like "123°45'67.89\""
    """
    degrees = int(longitude)
    minutes_float = (longitude - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    return f"{degrees:03d}{DEGREE_SYMBOL}{minutes:02d}{MINUTE_SYMBOL}{seconds:05.2f}{SECOND_SYMBOL}"


def format_latitude(lat: float) -> str:
    """Format geographic latitude with N/S suffix."""
    direction = "N" if lat >= 0 else "S"
    lat_abs = abs(lat)
    degrees = int(lat_abs)
    minutes_float = (lat_abs - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    return f"{degrees}{DEGREE_SYMBOL}{minutes:02d}{MINUTE_SYMBOL}{seconds:05.2f}{SECOND_SYMBOL}{direction}"


def format_longitude_geo(lon: float) -> str:
    """Format geographic longitude with E/W suffix."""
    direction = "E" if lon >= 0 else "W"
    lon_abs = abs(lon)
    degrees = int(lon_abs)
    minutes_float = (lon_abs - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    return f"{degrees}{DEGREE_SYMBOL}{minutes:02d}{MINUTE_SYMBOL}{seconds:05.2f}{SECOND_SYMBOL}{direction}"
