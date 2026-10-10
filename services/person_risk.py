"""Reusable missing-person risk classification rules."""

from collections.abc import Mapping
from typing import Any


RISK_LEVELS = ("low", "medium", "high", "critical")
RISK_PRIORITY = {level: priority for priority, level in enumerate(RISK_LEVELS)}
VULNERABLE_HOUSING_STATUSES = {"homeless", "unhoused", "transient"}
RISK_TEXT_FIELDS = (
    "description",
    "medical_conditions",
    "scars",
    "tattoos",
    "last_seen_location",
)
CRITICAL_TERMS = (
    "autism",
    "alzheimer",
    "dementia",
    "diabetic",
    "insulin",
    "medication",
    "medicine",
    "needs meds",
    "life saving",
    "lifesaving",
    "wheelchair",
    "disability",
    "disabled",
    "nonverbal",
    "cognitive",
    "developmental",
)
HIGH_RISK_TERMS = (
    "elderly",
    "child",
    "minor",
    "runaway",
    "pregnant",
    "injured",
    "hospital",
    "danger",
    "impaired",
    "limp",
)


def _normalized_risk_level(value: Any) -> str:
    level = str(value or "medium").strip().lower()
    return level if level in RISK_PRIORITY else "medium"


def _parsed_age(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        age = int(value)
    except (TypeError, ValueError):
        return None
    return age if age >= 0 else None


def _higher_risk(current: str, inferred: str) -> str:
    return inferred if RISK_PRIORITY[inferred] > RISK_PRIORITY[current] else current


def infer_missing_person_risk(data: Mapping[str, Any]) -> str:
    """Return the highest explicit or rule-inferred missing-person risk level."""
    current_risk = _normalized_risk_level(data.get("risk_level"))
    age = _parsed_age(data.get("age"))
    housing_status = str(data.get("housing_status") or "").strip().lower()
    risk_text = " ".join(str(data.get(field) or "") for field in RISK_TEXT_FIELDS).lower()

    if age is not None and (age <= 12 or age >= 65):
        return "critical"

    if any(term in risk_text for term in CRITICAL_TERMS):
        return "critical"

    if age is not None and age < 18:
        return _higher_risk(current_risk, "high")
    if housing_status in VULNERABLE_HOUSING_STATUSES:
        return _higher_risk(current_risk, "high")
    if any(term in risk_text for term in HIGH_RISK_TERMS):
        return _higher_risk(current_risk, "high")

    return current_risk
