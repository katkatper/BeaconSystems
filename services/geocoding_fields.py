from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


GEOCODE_FIELDS = {
    "latitude": "latitude",
    "longitude": "longitude",
    "provider": "geocode_provider",
    "accuracy": "geocode_accuracy",
    "score": "geocode_score",
    "formatted_address": "geocoded_address",
}


def utc_now() -> datetime:
    """Return UTC in the naive form expected by Beacon's current database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def apply_geocode_result(
    target: Any,
    result: dict[str, Any] | None,
    *,
    include_coordinates: bool = True,
    clear_when_missing: bool = False,
    timestamp: datetime | None = None,
) -> bool:
    """Copy normalized geocoder output onto a model-like object.

    Returns whether usable geocoding data was applied. Callers can preserve
    existing model values on a lookup failure or explicitly clear stale values.
    """
    if not result and not clear_when_missing:
        return False

    fields = GEOCODE_FIELDS
    if not include_coordinates:
        fields = {
            source: destination
            for source, destination in GEOCODE_FIELDS.items()
            if source not in {"latitude", "longitude"}
        }

    for source, destination in fields.items():
        setattr(target, destination, result.get(source) if result else None)

    target.geocoded_at = (timestamp or utc_now()) if result else None
    return bool(result)


def copy_geocode_fields(target: Any, source: Any) -> None:
    """Copy previously persisted geocode metadata between model-like objects."""
    for destination in GEOCODE_FIELDS.values():
        setattr(target, destination, getattr(source, destination, None))
    target.geocoded_at = getattr(source, "geocoded_at", None)
