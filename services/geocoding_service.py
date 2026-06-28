import re
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from config.settings import (
    ARCGIS_API_KEY,
    ARCGIS_GEOCODE_FOR_STORAGE,
    ARCGIS_GEOCODE_MIN_SCORE,
    ARCGIS_GEOCODE_TIMEOUT_SECONDS,
    ARCGIS_GEOCODE_URL,
    ARCGIS_GEOCODING_ENABLED,
)


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
    "bayside market place": (25.7783, -80.1860),
    "bayside marketplace": (25.7783, -80.1860),
    "1015 n america way miami fl 33132": (25.7778, -80.1799),
    "1015 north america way miami fl 33132": (25.7778, -80.1799),
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
    hash_value = 17

    for character in address:
        hash_value = (hash_value * 31 + ord(character)) % 1000003

    lat_seed = (hash_value % 997) / 997
    lon_seed = ((hash_value * 37) % 991) / 991

    return (lat_seed - 0.5) * 0.035, (lon_seed - 0.5) * 0.035


def _build_result(
    latitude: float,
    longitude: float,
    accuracy: str,
    provider: str,
    score: float | None = None,
    formatted_address: str | None = None,
):
    return {
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "provider": provider,
        "score": score,
        "formatted_address": formatted_address,
    }


def _arcgis_accuracy(addr_type: str | None, score: float | None) -> str:
    normalized_type = (addr_type or "").lower()

    if score is not None and score < ARCGIS_GEOCODE_MIN_SCORE:
        return "low_confidence"

    if normalized_type in {"pointaddress", "subaddress"}:
        return "rooftop"

    if normalized_type in {"streetaddress", "streetint", "streetname"}:
        return "street"

    if normalized_type in {"poi", "poilatlong"}:
        return "place"

    if normalized_type in {"locality", "city", "postal"}:
        return "area"

    return "arcgis_candidate"


def _geocode_with_arcgis(value: str):
    if not ARCGIS_GEOCODING_ENABLED or not ARCGIS_API_KEY:
        return None

    query = {
        "f": "json",
        "SingleLine": value,
        "outFields": "Match_addr,Addr_type,Score",
        "maxLocations": 1,
        "forStorage": str(ARCGIS_GEOCODE_FOR_STORAGE).lower(),
        "token": ARCGIS_API_KEY,
    }
    request_url = f"{ARCGIS_GEOCODE_URL}?{urlencode(query)}"

    try:
        with urlopen(request_url, timeout=ARCGIS_GEOCODE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return None

    candidates = payload.get("candidates") or []

    if not candidates:
        return None

    candidate = candidates[0]
    location = candidate.get("location") or {}
    attributes = candidate.get("attributes") or {}
    latitude = location.get("y")
    longitude = location.get("x")
    score = candidate.get("score", attributes.get("Score"))

    if latitude is None or longitude is None:
        return None

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        score = float(score) if score is not None else None
    except (TypeError, ValueError):
        return None

    if score is not None and score < ARCGIS_GEOCODE_MIN_SCORE:
        return None

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None

    formatted_address = (
        candidate.get("address")
        or attributes.get("Match_addr")
        or value
    )
    accuracy = _arcgis_accuracy(attributes.get("Addr_type"), score)

    return _build_result(
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        provider="arcgis",
        score=score,
        formatted_address=formatted_address,
    )


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
        return _build_result(
            latitude=latitude,
            longitude=longitude,
            accuracy="provided_coordinates",
            provider="manual",
            score=100,
            formatted_address=value,
        )

    arcgis_result = _geocode_with_arcgis(value)

    if arcgis_result:
        return arcgis_result

    if normalized in KNOWN_LOCATIONS:
        latitude, longitude = KNOWN_LOCATIONS[normalized]
        return _build_result(
            latitude=latitude,
            longitude=longitude,
            accuracy="known_address",
            provider="local",
            score=100,
            formatted_address=value,
        )

    for key, coordinates in KNOWN_LOCATIONS.items():
        if key in normalized or normalized in key:
            latitude, longitude = coordinates
            return _build_result(
                latitude=latitude,
                longitude=longitude,
                accuracy="known_place",
                provider="local",
                score=90,
                formatted_address=key,
            )

    for city, coordinates in CITY_CENTERS.items():
        if city in normalized:
            lat_offset, lon_offset = _deterministic_offset(normalized)
            return _build_result(
                latitude=coordinates[0] + lat_offset,
                longitude=coordinates[1] + lon_offset,
                accuracy="city_estimate",
                provider="local",
                score=60,
                formatted_address=city,
            )

    return None
