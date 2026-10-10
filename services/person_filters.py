"""Shared filters for missing-person collection queries."""

from collections.abc import Sequence
from datetime import datetime, time, timedelta

from sqlalchemy import or_


REPORTED_ON_FORMAT = "%Y-%m-%d"


def reported_day_bounds(reported_on: str) -> tuple[datetime, datetime]:
    """Return a half-open UTC-compatible day range for a YYYY-MM-DD value."""
    report_day = datetime.strptime(reported_on.strip(), REPORTED_ON_FORMAT).date()
    day_start = datetime.combine(report_day, time.min)
    return day_start, day_start + timedelta(days=1)


def apply_person_query_filters(
    query,
    *,
    search_text: str | None,
    search_columns: Sequence,
    reported_on: str | None,
    created_at_column,
):
    """Apply consistent optional text and reported-day filters to a query."""
    normalized_search = (search_text or "").strip()
    if normalized_search:
        search_pattern = f"%{normalized_search}%"
        query = query.filter(
            or_(*(column.ilike(search_pattern) for column in search_columns))
        )

    if reported_on:
        day_start, next_day_start = reported_day_bounds(reported_on)
        query = query.filter(
            created_at_column >= day_start,
            created_at_column < next_day_start,
        )

    return query
