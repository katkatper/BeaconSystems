"""Canonical normalization for approved external-provider observations.

Provider adapters map source-specific payloads into this stable contract so the
matching pipeline does not need to be rewritten for every partner.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

CANONICAL_FIELDS = {
    "subject_name",
    "location",
    "observed_at",
    "latitude",
    "longitude",
    "plate_number",
    "plate_state",
    "vehicle_make",
    "vehicle_model",
    "vehicle_color",
    "vehicle_year",
    "travel_direction",
    "camera_id",
    "image_url",
}


def normalize_identifier(value: Any) -> str | None:
    if value in (None, ""):
        return None
    normalized = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return normalized or None


def normalize_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    normalized = " ".join(str(value).strip().split())
    return normalized or None


def value_at_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def normalize_provider_payload(
    payload: dict[str, Any],
    field_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a canonical observation while retaining the original payload.

    Mapping keys are Beacon canonical field names and values are dotted paths in
    the provider payload, for example ``{"plate_number": "vehicle.plate"}``.
    Without a mapping, canonical top-level fields are accepted directly.
    """
    if not isinstance(payload, dict):
        raise TypeError("Provider payload must be a JSON object")

    mapping = field_mapping or {field: field for field in CANONICAL_FIELDS}
    unknown = set(mapping).difference(CANONICAL_FIELDS)
    if unknown:
        raise ValueError(f"Unsupported canonical fields: {', '.join(sorted(unknown))}")

    observation = {
        field: value_at_path(payload, path)
        for field, path in mapping.items()
        if isinstance(path, str) and path.strip()
    }
    observation["plate_number"] = normalize_identifier(observation.get("plate_number"))
    observation["plate_state"] = normalize_identifier(observation.get("plate_state"))
    for field in CANONICAL_FIELDS - {
        "plate_number",
        "plate_state",
        "latitude",
        "longitude",
        "vehicle_year",
    }:
        observation[field] = normalize_text(observation.get(field))

    for field in ("latitude", "longitude"):
        value = observation.get(field)
        if value not in (None, ""):
            observation[field] = float(value)
    year = observation.get("vehicle_year")
    if year not in (None, ""):
        observation["vehicle_year"] = int(year)

    observed_at = observation.get("observed_at")
    if observed_at:
        datetime.fromisoformat(observed_at.replace("Z", "+00:00"))

    observation["provider_payload"] = payload
    return observation
