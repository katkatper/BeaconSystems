from datetime import datetime

from services.case_numbering import (
    missing_person_case_prefix,
    select_missing_person_case_number,
)


OPENED_AT = datetime(2026, 10, 10, 12, 0, 0)


def test_missing_person_case_prefix_is_stable_and_zero_padded():
    assert missing_person_case_prefix(42, OPENED_AT) == "MP-2026-000042"


def test_base_number_is_used_when_available():
    assert select_missing_person_case_number(42, [], OPENED_AT) == "MP-2026-000042"


def test_first_duplicate_uses_suffix_two():
    assert (
        select_missing_person_case_number(42, ["MP-2026-000042"], OPENED_AT)
        == "MP-2026-000042-2"
    )


def test_first_available_suffix_is_selected():
    existing = {
        "MP-2026-000042",
        "MP-2026-000042-2",
        "MP-2026-000042-3",
        "MP-2026-999999",
    }

    assert select_missing_person_case_number(42, existing, OPENED_AT) == "MP-2026-000042-4"


def test_generator_input_is_supported():
    existing = (number for number in ["MP-2026-000042", "MP-2026-000042-2"])
    assert select_missing_person_case_number(42, existing, OPENED_AT) == "MP-2026-000042-3"
