from typing import Any


HIGH_CONFIDENCE_TERMS = (
    "confirmed",
    "identified",
    "license plate",
    "plate",
    "photo",
    "video",
    "cctv",
    "camera",
    "lpr",
    "facial recognition",
    "positive id",
    "same clothes",
)
MEDIUM_CONFIDENCE_TERMS = (
    "witness",
    "saw",
    "seen",
    "reported",
    "vehicle",
    "direction",
    "walking",
    "running",
    "near",
    "matching description",
)
LOW_CONFIDENCE_TERMS = (
    "possible",
    "maybe",
    "unknown",
    "unclear",
    "unconfirmed",
    "similar",
    "rumor",
)


def _term_adjustment(text: str, terms: tuple[str, ...], weight: float) -> float:
    return sum(weight for term in terms if term in text)


def _geocode_adjustment(geocoded: dict[str, Any] | None) -> float:
    if not geocoded:
        return 0

    accuracy = geocoded.get("accuracy")
    if accuracy in {"rooftop", "known_address", "provided_coordinates"}:
        adjustment = 0.14
    elif accuracy in {"street", "known_place", "place"}:
        adjustment = 0.1
    elif accuracy in {"city_estimate", "area"}:
        adjustment = -0.06
    else:
        adjustment = 0

    try:
        provider_score = float(geocoded.get("score"))
    except (TypeError, ValueError):
        return adjustment

    return adjustment + max(-0.05, min(0.1, (provider_score - 80) / 200))


def calculate_sighting_confidence(
    description: str | None,
    location: str | None,
    geocoded: dict[str, Any] | None = None,
) -> float:
    """Return a bounded, explainable heuristic confidence score for a sighting."""
    text = f"{description or ''} {location or ''}".lower()
    score = 0.35
    score += _term_adjustment(text, HIGH_CONFIDENCE_TERMS, 0.12)
    score += _term_adjustment(text, MEDIUM_CONFIDENCE_TERMS, 0.06)
    score += _term_adjustment(text, LOW_CONFIDENCE_TERMS, -0.07)
    score += _geocode_adjustment(geocoded)
    if len(text.strip()) < 24:
        score -= 0.08
    return round(max(0.1, min(0.95, score)), 2)
