from datetime import datetime
from unittest.mock import Mock

import pytest

from models.person import Person
from services.person_filters import apply_person_query_filters, reported_day_bounds


def test_reported_day_bounds_use_half_open_range():
    assert reported_day_bounds("2026-10-10") == (
        datetime(2026, 10, 10),
        datetime(2026, 10, 11),
    )


def test_reported_day_bounds_handle_year_boundary_and_whitespace():
    assert reported_day_bounds(" 2026-12-31 ") == (
        datetime(2026, 12, 31),
        datetime(2027, 1, 1),
    )


@pytest.mark.parametrize("value", ["10/10/2026", "2026-02-30", "", "not-a-date"])
def test_reported_day_bounds_reject_invalid_values(value):
    with pytest.raises(ValueError):
        reported_day_bounds(value)


def test_blank_search_does_not_add_a_database_filter():
    query = Mock()

    result = apply_person_query_filters(
        query,
        search_text="   ",
        search_columns=(Person.first_name, Person.last_name),
        reported_on=None,
        created_at_column=Person.created_at,
    )

    assert result is query
    query.filter.assert_not_called()


def test_search_and_date_filters_are_both_applied():
    query = Mock()
    query.filter.return_value = query

    result = apply_person_query_filters(
        query,
        search_text="  Morgan  ",
        search_columns=(Person.first_name, Person.last_name),
        reported_on="2026-10-10",
        created_at_column=Person.created_at,
    )

    assert result is query
    assert query.filter.call_count == 2
