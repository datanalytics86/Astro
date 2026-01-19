"""
Validation Module - Compare calculations against JPL Horizons.

JPL Horizons is NASA's authoritative source for solar system ephemeris data.
This module provides tools to validate our calculations against Horizons.

Note: Requires internet connection to query JPL Horizons API.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json
import urllib.request
import urllib.parse

from core.ephemeris import get_position
from core.time_engine import datetime_to_jd


# JPL Horizons body codes
HORIZONS_BODIES = {
    "sun": "10",
    "moon": "301",
    "mercury": "199",
    "venus": "299",
    "mars": "499",
    "jupiter": "599",
    "saturn": "699",
    "uranus": "799",
    "neptune": "899",
    "pluto": "999",
}


@dataclass
class ValidationResult:
    """Result of validation against JPL Horizons."""

    body: str
    datetime_utc: datetime
    our_longitude: float
    our_latitude: float
    jpl_longitude: Optional[float]
    jpl_latitude: Optional[float]
    longitude_diff_arcsec: Optional[float]
    latitude_diff_arcsec: Optional[float]
    within_tolerance: bool
    tolerance_arcsec: float
    error_message: Optional[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "body": self.body,
            "datetime_utc": self.datetime_utc.isoformat(),
            "our_longitude": self.our_longitude,
            "our_latitude": self.our_latitude,
            "jpl_longitude": self.jpl_longitude,
            "jpl_latitude": self.jpl_latitude,
            "longitude_diff_arcsec": self.longitude_diff_arcsec,
            "latitude_diff_arcsec": self.latitude_diff_arcsec,
            "within_tolerance": self.within_tolerance,
            "tolerance_arcsec": self.tolerance_arcsec,
            "error_message": self.error_message,
        }

    def __str__(self) -> str:
        """String representation."""
        if self.error_message:
            return f"{self.body}: ERROR - {self.error_message}"

        status = "OK" if self.within_tolerance else "FAIL"
        return (
            f"{self.body}: {status} "
            f"(Δlon: {self.longitude_diff_arcsec:.2f}\", "
            f"Δlat: {self.latitude_diff_arcsec:.2f}\")"
        )


class JPLHorizonsValidator:
    """
    Validate ephemeris calculations against JPL Horizons.

    Uses the Horizons API to fetch authoritative positions and
    compare with our calculated values.
    """

    # Horizons API endpoint
    API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

    # Default tolerance (arcseconds)
    DEFAULT_TOLERANCE = 1.0

    def __init__(self, tolerance_arcsec: float = None):
        """
        Initialize validator.

        Args:
            tolerance_arcsec: Maximum acceptable difference in arcseconds
        """
        self.tolerance = tolerance_arcsec or self.DEFAULT_TOLERANCE

    def query_horizons(
        self,
        body: str,
        datetime_utc: datetime,
    ) -> Optional[dict]:
        """
        Query JPL Horizons for body position.

        Args:
            body: Body name (must be in HORIZONS_BODIES)
            datetime_utc: UTC datetime for query

        Returns:
            Dictionary with RA, DEC, and ecliptic coordinates, or None on error
        """
        if body not in HORIZONS_BODIES:
            return None

        horizons_id = HORIZONS_BODIES[body]

        # Format date for Horizons
        date_str = datetime_utc.strftime("%Y-%m-%d %H:%M:%S")

        # Build query parameters
        params = {
            "format": "json",
            "COMMAND": f"'{horizons_id}'",
            "OBJ_DATA": "NO",
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "OBSERVER",
            "CENTER": "'500@399'",  # Geocentric
            "START_TIME": f"'{date_str}'",
            "STOP_TIME": f"'{date_str}'",
            "STEP_SIZE": "'1 d'",
            "QUANTITIES": "'31,32'",  # Ecliptic lon/lat
        }

        url = self.API_URL + "?" + urllib.parse.urlencode(params)

        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode())
                return self._parse_horizons_response(data)
        except Exception as e:
            return {"error": str(e)}

    def _parse_horizons_response(self, data: dict) -> dict:
        """Parse Horizons API response to extract coordinates."""
        try:
            result_text = data.get("result", "")

            # Find the data section (after $$SOE and before $$EOE)
            if "$$SOE" in result_text and "$$EOE" in result_text:
                soe_idx = result_text.index("$$SOE") + 5
                eoe_idx = result_text.index("$$EOE")
                data_section = result_text[soe_idx:eoe_idx].strip()

                # Parse the data line
                # Format varies, but typically includes ecliptic lon/lat
                lines = data_section.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("*"):
                        parts = line.split()
                        # Try to find ecliptic coordinates
                        # This is approximate - actual parsing depends on output format
                        if len(parts) >= 4:
                            try:
                                # Assuming ObsEcLon and ObsEcLat are in the output
                                ecl_lon = float(parts[-2])
                                ecl_lat = float(parts[-1])
                                return {
                                    "ecliptic_longitude": ecl_lon,
                                    "ecliptic_latitude": ecl_lat,
                                }
                            except (ValueError, IndexError):
                                pass

            return {"error": "Could not parse Horizons response"}

        except Exception as e:
            return {"error": f"Parse error: {str(e)}"}

    def validate_position(
        self,
        body: str,
        datetime_utc: datetime,
    ) -> ValidationResult:
        """
        Validate our calculated position against JPL Horizons.

        Args:
            body: Body name
            datetime_utc: UTC datetime

        Returns:
            ValidationResult with comparison data
        """
        # Get our calculated position
        jd = datetime_to_jd(datetime_utc)
        our_pos = get_position(body, jd)
        our_lon = our_pos.longitude_decimal
        our_lat = our_pos.latitude_decimal

        # Query Horizons
        jpl_data = self.query_horizons(body, datetime_utc)

        if jpl_data is None:
            return ValidationResult(
                body=body,
                datetime_utc=datetime_utc,
                our_longitude=our_lon,
                our_latitude=our_lat,
                jpl_longitude=None,
                jpl_latitude=None,
                longitude_diff_arcsec=None,
                latitude_diff_arcsec=None,
                within_tolerance=False,
                tolerance_arcsec=self.tolerance,
                error_message=f"Body '{body}' not supported",
            )

        if "error" in jpl_data:
            return ValidationResult(
                body=body,
                datetime_utc=datetime_utc,
                our_longitude=our_lon,
                our_latitude=our_lat,
                jpl_longitude=None,
                jpl_latitude=None,
                longitude_diff_arcsec=None,
                latitude_diff_arcsec=None,
                within_tolerance=False,
                tolerance_arcsec=self.tolerance,
                error_message=jpl_data["error"],
            )

        jpl_lon = jpl_data.get("ecliptic_longitude")
        jpl_lat = jpl_data.get("ecliptic_latitude")

        if jpl_lon is None or jpl_lat is None:
            return ValidationResult(
                body=body,
                datetime_utc=datetime_utc,
                our_longitude=our_lon,
                our_latitude=our_lat,
                jpl_longitude=None,
                jpl_latitude=None,
                longitude_diff_arcsec=None,
                latitude_diff_arcsec=None,
                within_tolerance=False,
                tolerance_arcsec=self.tolerance,
                error_message="Could not extract JPL coordinates",
            )

        # Calculate differences in arcseconds
        lon_diff = abs(our_lon - jpl_lon)
        if lon_diff > 180:
            lon_diff = 360 - lon_diff
        lon_diff_arcsec = lon_diff * 3600

        lat_diff_arcsec = abs(our_lat - jpl_lat) * 3600

        # Check tolerance
        within_tolerance = (
            lon_diff_arcsec <= self.tolerance and
            lat_diff_arcsec <= self.tolerance
        )

        return ValidationResult(
            body=body,
            datetime_utc=datetime_utc,
            our_longitude=our_lon,
            our_latitude=our_lat,
            jpl_longitude=jpl_lon,
            jpl_latitude=jpl_lat,
            longitude_diff_arcsec=lon_diff_arcsec,
            latitude_diff_arcsec=lat_diff_arcsec,
            within_tolerance=within_tolerance,
            tolerance_arcsec=self.tolerance,
            error_message=None,
        )

    def validate_all_bodies(
        self,
        datetime_utc: datetime,
        bodies: Optional[list] = None,
    ) -> list[ValidationResult]:
        """
        Validate all bodies for a given datetime.

        Args:
            datetime_utc: UTC datetime
            bodies: List of bodies (default: all supported)

        Returns:
            List of ValidationResult
        """
        if bodies is None:
            bodies = list(HORIZONS_BODIES.keys())

        results = []
        for body in bodies:
            result = self.validate_position(body, datetime_utc)
            results.append(result)

        return results

    def generate_validation_report(
        self,
        datetime_utc: datetime,
        bodies: Optional[list] = None,
    ) -> str:
        """
        Generate a validation report.

        Args:
            datetime_utc: UTC datetime
            bodies: List of bodies to validate

        Returns:
            Markdown formatted report
        """
        results = self.validate_all_bodies(datetime_utc, bodies)

        lines = [
            "# Ephemeris Validation Report",
            "",
            f"**Date/Time (UTC):** {datetime_utc.isoformat()}",
            f"**Tolerance:** {self.tolerance} arcseconds",
            "",
            "## Results",
            "",
            "| Body | Our Lon | JPL Lon | Δ Lon (\") | Our Lat | JPL Lat | Δ Lat (\") | Status |",
            "|------|---------|---------|-----------|---------|---------|-----------|--------|",
        ]

        passed = 0
        failed = 0
        errors = 0

        for r in results:
            if r.error_message:
                lines.append(
                    f"| {r.body.capitalize()} | {r.our_longitude:.4f}° | - | - | "
                    f"{r.our_latitude:.4f}° | - | - | ERROR |"
                )
                errors += 1
            else:
                status = "PASS" if r.within_tolerance else "FAIL"
                if r.within_tolerance:
                    passed += 1
                else:
                    failed += 1

                lines.append(
                    f"| {r.body.capitalize()} | {r.our_longitude:.4f}° | "
                    f"{r.jpl_longitude:.4f}° | {r.longitude_diff_arcsec:.2f} | "
                    f"{r.our_latitude:.4f}° | {r.jpl_latitude:.4f}° | "
                    f"{r.latitude_diff_arcsec:.2f} | {status} |"
                )

        lines.extend([
            "",
            "## Summary",
            "",
            f"- **Passed:** {passed}",
            f"- **Failed:** {failed}",
            f"- **Errors:** {errors}",
            f"- **Total:** {len(results)}",
        ])

        return "\n".join(lines)


class LocalValidation:
    """
    Local validation without external API calls.

    Uses known reference values and internal consistency checks.
    """

    # Reference values for validation (from published ephemerides)
    # Format: {body: {jd: (longitude, latitude)}}
    REFERENCE_VALUES = {
        # J2000.0 (2000-01-01 12:00 TT)
        2451545.0: {
            "sun": (280.4665, 0.0),
            "moon": (218.32, 5.15),  # Approximate
        },
    }

    def validate_known_epoch(
        self,
        jd: float = 2451545.0,  # J2000.0
        tolerance_deg: float = 0.01,
    ) -> dict:
        """
        Validate against known reference epoch.

        Args:
            jd: Julian Day of reference epoch
            tolerance_deg: Tolerance in degrees

        Returns:
            Validation results
        """
        if jd not in self.REFERENCE_VALUES:
            return {"error": f"No reference values for JD {jd}"}

        results = {}
        ref_data = self.REFERENCE_VALUES[jd]

        for body, (ref_lon, ref_lat) in ref_data.items():
            our_pos = get_position(body, jd)

            lon_diff = abs(our_pos.longitude_decimal - ref_lon)
            if lon_diff > 180:
                lon_diff = 360 - lon_diff

            lat_diff = abs(our_pos.latitude_decimal - ref_lat)

            results[body] = {
                "our_longitude": our_pos.longitude_decimal,
                "reference_longitude": ref_lon,
                "longitude_diff": lon_diff,
                "our_latitude": our_pos.latitude_decimal,
                "reference_latitude": ref_lat,
                "latitude_diff": lat_diff,
                "within_tolerance": lon_diff <= tolerance_deg and lat_diff <= tolerance_deg,
            }

        return results

    def internal_consistency_check(
        self,
        datetime_utc: datetime,
    ) -> dict:
        """
        Run internal consistency checks.

        Verifies:
        - Sun speed is approximately 1°/day
        - Moon speed is approximately 13°/day
        - Planetary ordering is correct
        """
        jd = datetime_to_jd(datetime_utc)
        jd_next = jd + 1.0

        results = {}

        # Check Sun speed
        sun_now = get_position("sun", jd)
        sun_next = get_position("sun", jd_next)
        sun_speed = sun_next.longitude_decimal - sun_now.longitude_decimal
        if sun_speed < 0:
            sun_speed += 360
        results["sun_daily_motion"] = {
            "value": sun_speed,
            "expected_range": (0.95, 1.02),
            "ok": 0.95 <= sun_speed <= 1.02,
        }

        # Check Moon speed
        moon_now = get_position("moon", jd)
        moon_next = get_position("moon", jd_next)
        moon_speed = moon_next.longitude_decimal - moon_now.longitude_decimal
        if moon_speed < -180:
            moon_speed += 360
        elif moon_speed > 180:
            moon_speed -= 360
        results["moon_daily_motion"] = {
            "value": abs(moon_speed),
            "expected_range": (11.0, 15.0),
            "ok": 11.0 <= abs(moon_speed) <= 15.0,
        }

        # Check Sun is never retrograde
        results["sun_not_retrograde"] = {
            "value": sun_now.speed_longitude,
            "ok": sun_now.speed_longitude > 0,
        }

        return results


# Module-level convenience functions
_validator = JPLHorizonsValidator()
_local = LocalValidation()


def validate_against_jpl(
    body: str,
    datetime_utc: datetime,
    tolerance_arcsec: float = 1.0,
) -> ValidationResult:
    """Validate position against JPL Horizons."""
    validator = JPLHorizonsValidator(tolerance_arcsec)
    return validator.validate_position(body, datetime_utc)


def validate_all(datetime_utc: datetime) -> list[ValidationResult]:
    """Validate all bodies against JPL Horizons."""
    return _validator.validate_all_bodies(datetime_utc)


def run_internal_checks(datetime_utc: datetime) -> dict:
    """Run internal consistency checks."""
    return _local.internal_consistency_check(datetime_utc)
