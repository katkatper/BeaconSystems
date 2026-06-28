import hashlib
import re


KNOWN_LOCATIONS = {
    "1001 california st houston tx 77006": (29.7436, -95.3913),
    "montrose library": (29.7436, -95.3913),
    "2510 willowick rd houston tx 77027": (29.7418, -95.4502),
    "2510 willowick road houston tx 77027": (29.7418, -95.4502),
    "1200 travis street houston tx 77002": (29.7543, -95.3670),
    "715 e 8th street austin tx 78701": (30.2718, -97.7345),
    "1400 botham jean blvd dallas tx 75215": (32.7696, -96.7954),
    "12230 west road houston tx 77065": (29.9147, -95.6040),
    "5805 north lamar blvd austin tx 78752": (30.3254, -97.7247),
    "5700 east northwest highway dallas tx 75231": (32.8648, -96.7676),
}

CITY_CENTERS = {
    "houston": (29.7604, -95.3698),
    "dallas": (32.7767, -96.7970),
    "austin": (30.2672, -97.7431),
    "san antonio": (29.4241, -98.4936),
    "el paso": (31.7619, -106.4850),
    "fort worth": (32.7555, -97.3308),
    "miami": (25.7617, -80.1918),
}


def normalize_address(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def parse_coordinate_pair(value: str | None):
    if not value:
        return None

    match = re.fullmatch(
        r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*",
        value,
    )

    if not match:
        return None

    latitude = float(match.group(1))
    longitude = float(match.group(2))

    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
        return latitude, longitude

    return None


def _deterministic_offset(address: str) -> tuple[float, float]:
    digest = hashlib.sha256(address.encode("utf-8")).hexdigest()
    lat_seed = int(digest[:8], 16) / 0xFFFFFFFF
    lon_seed = int(digest[8:16], 16) / 0xFFFFFFFF

    return (lat_seed - 0.5) * 0.035, (lon_seed - 0.5) * 0.035


def geocode_address(value: str | None):
    """Return approximate coordinates for a usable map point.

    Local development uses known addresses and city-level fallbacks. Production
    can replace this service with an approved geocoder without changing callers.
    """
    normalized = normalize_address(value)

    if not normalized:
        return None

    parsed_coordinates = parse_coordinate_pair(value)

    if parsed_coordinates:
        latitude, longitude = parsed_coordinates
        return {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": "provided_coordinates",
        }

    if normalized in KNOWN_LOCATIONS:
        latitude, longitude = KNOWN_LOCATIONS[normalized]
        return {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": "known_address",
        }

    for key, coordinates in KNOWN_LOCATIONS.items():
        if key in normalized or normalized in key:
            latitude, longitude = coordinates
            return {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": "known_place",
            }

    for city, coordinates in CITY_CENTERS.items():
        if city in normalized:
            lat_offset, lon_offset = _deterministic_offset(normalized)
            return {
                "latitude": coordinates[0] + lat_offset,
                "longitude": coordinates[1] + lon_offset,
                "accuracy": "city_estimate",
            }

    return None
