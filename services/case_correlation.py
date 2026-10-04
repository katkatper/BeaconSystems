import json
import re
from typing import Any


def normalize_correlation_value(value: Any) -> str:
    """Normalize comparison values without preserving punctuation or spacing."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def parse_associate_names(raw_value: str | None) -> set[str]:
    """Read current JSON and legacy semicolon-delimited associate formats."""
    if not raw_value:
        return set()

    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {
            normalized
            for entry in raw_value.split(";")
            if entry.strip()
            if (normalized := normalize_correlation_value(entry.split("|")[0]))
        }

    entries = parsed if isinstance(parsed, list) else [parsed]
    return {
        normalized
        for entry in entries
        if isinstance(entry, dict)
        if (name := entry.get("name") or entry.get("associate"))
        if (normalized := normalize_correlation_value(name))
    }


def associate_name_matches(target_person: Any, other_person: Any) -> set[str]:
    """Return normalized associate identities shared by two person profiles."""
    target_associates = parse_associate_names(target_person.known_associates)
    other_associates = parse_associate_names(other_person.known_associates)
    target_name = normalize_correlation_value(
        f"{target_person.first_name} {target_person.last_name}"
    )
    other_name = normalize_correlation_value(
        f"{other_person.first_name} {other_person.last_name}"
    )

    direct_overlap = set()
    if other_name and other_name in target_associates:
        direct_overlap.add(other_name)
    if target_name and target_name in other_associates:
        direct_overlap.add(target_name)

    return target_associates.intersection(other_associates) | direct_overlap


def _location_entries(person: Any, sightings: list[Any], records: list[Any]):
    return [
        ("Last seen location", person.last_seen_location),
        ("Home address", person.primary_address),
        *[("Sighting location", item.location) for item in sightings],
        *[
            (
                "External intelligence location",
                item.geocoded_address or item.location,
            )
            for item in records
        ],
    ]


def build_case_correlations(
    target_case: Any,
    accessible_cases: list[Any],
    people: dict[int, Any],
    sightings: list[Any],
    external_records: list[Any],
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Build explainable correlations from already authorized, bounded records."""
    target_person = people.get(target_case.person_id)
    if target_person is None:
        return []

    case_lookup = {case.case_id: case for case in accessible_cases}
    target_sightings = [
        item for item in sightings if item.case_id == target_case.case_id
    ]
    target_records = [
        item for item in external_records if item.case_id == target_case.case_id
    ]
    target_locations = {
        normalized: (label, value)
        for label, value in _location_entries(
            target_person,
            target_sightings,
            target_records,
        )
        if (normalized := normalize_correlation_value(value))
    }
    correlations: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int, str]] = set()

    for other_case in accessible_cases:
        if other_case.case_id == target_case.case_id:
            continue
        other_person = people.get(other_case.person_id)
        if other_person is None:
            continue

        other_sightings = [
            item for item in sightings if item.case_id == other_case.case_id
        ]
        other_records = [
            item for item in external_records if item.case_id == other_case.case_id
        ]
        for other_label, other_value in _location_entries(
            other_person,
            other_sightings,
            other_records,
        ):
            normalized = normalize_correlation_value(other_value)
            if not normalized or normalized not in target_locations:
                continue
            key = ("shared_location", other_case.case_id, normalized)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            target_label, displayed_value = target_locations[normalized]
            repeated_sighting = (
                target_label == "Sighting location"
                and other_label == "Sighting location"
            )
            correlations.append({
                "id": f"shared-location-{other_case.case_id}-{len(correlations)}",
                "type": "shared_location",
                "title": "Two investigations share a reported location",
                "summary": (
                    f"{target_case.case_number} and {other_case.case_number} "
                    f"both reference {displayed_value}."
                ),
                "linked_case_id": other_case.case_id,
                "linked_case_number": other_case.case_number,
                "confidence": 0.94 if repeated_sighting else 0.86,
                "explanation": (
                    "Exact normalized location match across authorized case records."
                ),
                "evidence": [
                    {
                        "case_number": target_case.case_number,
                        "source": target_label,
                        "value": displayed_value,
                    },
                    {
                        "case_number": other_case.case_number,
                        "source": other_label,
                        "value": other_value,
                    },
                ],
            })

        target_vehicle = normalize_correlation_value(target_person.vehicles)
        other_vehicle = normalize_correlation_value(other_person.vehicles)
        if target_vehicle and target_vehicle == other_vehicle:
            correlations.append({
                "id": f"shared-vehicle-{other_case.case_id}",
                "type": "shared_vehicle",
                "title": "Vehicle appears in separate investigations",
                "summary": (
                    f"{target_case.case_number} and {other_case.case_number} "
                    "contain the same vehicle intelligence."
                ),
                "linked_case_id": other_case.case_id,
                "linked_case_number": other_case.case_number,
                "confidence": 0.92,
                "explanation": (
                    "Exact normalized vehicle description match. Investigators "
                    "should verify plate, VIN, and ownership before acting."
                ),
                "evidence": [
                    {
                        "case_number": target_case.case_number,
                        "source": "Person vehicle intelligence",
                        "value": target_person.vehicles,
                    },
                    {
                        "case_number": other_case.case_number,
                        "source": "Person vehicle intelligence",
                        "value": other_person.vehicles,
                    },
                ],
            })

        if associate_name_matches(target_person, other_person):
            correlations.append({
                "id": f"shared-associate-{other_case.case_id}",
                "type": "shared_associate",
                "title": "Associate appears in another active investigation",
                "summary": (
                    f"A person relationship overlaps {target_case.case_number} "
                    f"and {other_case.case_number}."
                ),
                "linked_case_id": other_case.case_id,
                "linked_case_number": other_case.case_number,
                "confidence": 0.9,
                "explanation": (
                    "Exact normalized associate-name match across authorized "
                    "person profiles."
                ),
                "evidence": [
                    {
                        "case_number": target_case.case_number,
                        "source": "Known associates",
                        "value": target_person.known_associates,
                    },
                    {
                        "case_number": other_case.case_number,
                        "source": "Known associates",
                        "value": other_person.known_associates,
                    },
                ],
            })

    identifying_terms = [
        target_person.scars,
        target_person.tattoos,
        target_person.medical_conditions,
    ]
    for record in external_records:
        if (
            record.case_id == target_case.case_id
            or "hospital" not in str(record.record_type or "").lower()
        ):
            continue
        factors = []
        if target_person.age is not None and record.age == target_person.age:
            factors.append("age")
        record_text = str(record.notes or "").lower()
        if any(term and str(term).lower() in record_text for term in identifying_terms):
            factors.append("distinguishing characteristic")
        if not factors:
            continue

        linked_case = case_lookup.get(record.case_id)
        confidence = (
            0.62
            + (0.18 if "age" in factors else 0)
            + (0.15 if len(factors) > 1 else 0)
        )
        correlations.append({
            "id": f"hospital-match-{record.id}",
            "type": "hospital_demographic_match",
            "title": "Hospital record may match the missing person",
            "summary": (
                f"A hospital inquiry matches {', '.join(factors)} for "
                f"{target_case.case_number}."
            ),
            "linked_case_id": record.case_id,
            "linked_case_number": linked_case.case_number if linked_case else None,
            "confidence": min(confidence, 0.95),
            "explanation": (
                "Demographic and distinguishing-characteristic comparison; "
                "identity is not confirmed."
            ),
            "evidence": [
                {
                    "case_number": target_case.case_number,
                    "source": "Missing person profile",
                    "value": (
                        f"Age {target_person.age}; {target_person.scars or ''} "
                        f"{target_person.tattoos or ''}"
                    ).strip(),
                },
                {
                    "case_number": (
                        linked_case.case_number if linked_case else "Hospital record"
                    ),
                    "source": record.record_type,
                    "value": record.notes or record.location,
                },
            ],
        })

    correlations.sort(key=lambda item: item["confidence"], reverse=True)
    return correlations[:limit]
