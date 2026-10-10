import pytest

from services.person_risk import infer_missing_person_risk


@pytest.mark.parametrize("age", [0, 12, 65, 91, "70"])
def test_vulnerable_age_is_critical(age):
    assert infer_missing_person_risk({"age": age}) == "critical"


@pytest.mark.parametrize("field", ["description", "medical_conditions", "last_seen_location"])
def test_critical_medical_language_is_detected_across_fields(field):
    assert infer_missing_person_risk({field: "Person is diabetic and needs insulin"}) == "critical"


def test_minor_is_high_risk():
    assert infer_missing_person_risk({"age": 16}) == "high"


@pytest.mark.parametrize("housing_status", ["homeless", "UNHOUSED", " transient "])
def test_vulnerable_housing_status_is_high_risk(housing_status):
    assert infer_missing_person_risk({"housing_status": housing_status}) == "high"


def test_high_risk_language_is_detected():
    assert infer_missing_person_risk({"description": "Reported injured near hospital"}) == "high"


def test_explicit_risk_is_never_downgraded():
    assert infer_missing_person_risk({"risk_level": "critical", "age": 16}) == "critical"


@pytest.mark.parametrize("age", [None, "unknown", -1, True])
def test_unusable_age_does_not_break_classification(age):
    assert infer_missing_person_risk({"age": age}) == "medium"


def test_invalid_explicit_risk_uses_safe_default():
    assert infer_missing_person_risk({"risk_level": "urgent"}) == "medium"


def test_explicit_low_risk_is_preserved_without_stronger_signal():
    assert infer_missing_person_risk({"risk_level": " LOW "}) == "low"
