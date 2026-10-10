"""Deterministic case-number generation helpers."""

from collections.abc import Iterable
from datetime import datetime

from services.clock import utc_now


def missing_person_case_prefix(person_id: int, opened_at: datetime | None = None) -> str:
    """Return the stable base case number for a missing-person record."""
    year = (opened_at or utc_now()).year
    return f"MP-{year}-{person_id:06d}"


def select_missing_person_case_number(
    person_id: int,
    existing_case_numbers: Iterable[str],
    opened_at: datetime | None = None,
) -> str:
    """Choose the first available number without making repeated database queries."""
    base_number = missing_person_case_prefix(person_id, opened_at)
    existing = set(existing_case_numbers)
    if base_number not in existing:
        return base_number

    suffix = 2
    while f"{base_number}-{suffix}" in existing:
        suffix += 1
    return f"{base_number}-{suffix}"
