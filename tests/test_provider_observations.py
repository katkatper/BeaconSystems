from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routes.integrations_routes import serialize_integration_source
from routes.partner_intake_routes import (
    authenticate_partner_source,
    authorize_partner_destination,
)
from security.auth import hash_password
from security.partner_tokens import hash_partner_token
from services.partner_matching import score_bolo_vehicle_match
from services.provider_observations import (
    normalize_identifier,
    normalize_provider_payload,
)


def test_provider_mapping_normalizes_nested_toll_camera_payload():
    payload = {
        "event": {"capturedAt": "2026-10-25T13:45:00Z"},
        "vehicle": {
            "plate": " tx-abc 123 ",
            "state": "tx",
            "make": "Ford",
            "model": "F-150",
            "color": "Blue",
            "year": "2022",
        },
        "camera": {"id": "TOLL-44", "direction": "northbound"},
    }
    mapping = {
        "observed_at": "event.capturedAt",
        "plate_number": "vehicle.plate",
        "plate_state": "vehicle.state",
        "vehicle_make": "vehicle.make",
        "vehicle_model": "vehicle.model",
        "vehicle_color": "vehicle.color",
        "vehicle_year": "vehicle.year",
        "camera_id": "camera.id",
        "travel_direction": "camera.direction",
    }

    observation = normalize_provider_payload(payload, mapping)

    assert observation["plate_number"] == "TXABC123"
    assert observation["plate_state"] == "TX"
    assert observation["vehicle_year"] == 2022
    assert observation["camera_id"] == "TOLL-44"
    assert observation["provider_payload"] == payload


def test_vehicle_match_is_explainable_and_high_confidence_for_exact_plate():
    bolo = SimpleNamespace(
        plate_number="ABC-123",
        plate_state="TX",
        vehicle_make="Ford",
        vehicle_model="F-150",
        vehicle_color="Blue",
        vehicle_year=2022,
    )
    observation = {
        "plate_number": "ABC123",
        "plate_state": "TX",
        "vehicle_make": "ford",
        "vehicle_model": "f-150",
        "vehicle_color": "blue",
        "vehicle_year": 2022,
    }

    score, reasons = score_bolo_vehicle_match(bolo, observation)

    assert score == 100
    assert "license plate matched exactly" in reasons
    assert "vehicle make matched" in reasons


def test_vehicle_match_does_not_infer_from_partial_plate():
    bolo = SimpleNamespace(
        plate_number="ABC123",
        plate_state="TX",
        vehicle_make=None,
        vehicle_model=None,
        vehicle_color=None,
        vehicle_year=None,
    )

    score, reasons = score_bolo_vehicle_match(
        bolo,
        {"plate_number": "ABC12", "plate_state": "TX"},
    )

    assert score == 5
    assert "license plate matched exactly" not in reasons


def test_unknown_canonical_field_is_rejected():
    with pytest.raises(ValueError, match="Unsupported canonical fields"):
        normalize_provider_payload({"plate": "ABC123"}, {"secret": "plate"})


def test_identifier_normalization_handles_empty_values():
    assert normalize_identifier(None) is None
    assert normalize_identifier("---") is None


def test_source_specific_webhook_credential_is_enforced():
    source = SimpleNamespace(webhook_secret_hash=hash_partner_token("a" * 32))

    authenticate_partner_source(source, "a" * 32)
    with pytest.raises(HTTPException, match="Invalid partner webhook token"):
        authenticate_partner_source(source, "b" * 32)


def test_legacy_bcrypt_provider_credential_remains_valid_until_rotation():
    source = SimpleNamespace(webhook_secret_hash=hash_password("a" * 32))

    authenticate_partner_source(source, "a" * 32)


def test_source_serialization_never_exposes_webhook_hash():
    source = SimpleNamespace(
        id=7,
        name="Regional Toll Authority",
        source_type="toll",
        status="approved",
        is_active=True,
        api_url="https://partner.invalid/events",
        description="Authorized vehicle observations",
        adapter_key="canonical_v1",
        field_mapping={"plate_number": "vehicle.plate"},
        allowed_record_types=["vehicle_observation"],
        authorized_agencies=[SimpleNamespace(agency_id=12)],
        match_threshold=60,
        webhook_secret_hash="secret-hash",
        created_at=None,
    )

    serialized = serialize_integration_source(source)

    assert serialized["webhook_configured"] is True
    assert "webhook_secret_hash" not in serialized


def test_source_specific_webhook_is_tenant_destination_scoped():
    source = SimpleNamespace(
        webhook_secret_hash="configured",
        authorized_agencies=[
            SimpleNamespace(agency_id=12),
            SimpleNamespace(agency_id=13),
        ],
    )

    authorize_partner_destination(source, 12)
    with pytest.raises(HTTPException, match="not authorized"):
        authorize_partner_destination(source, 99)

    source.authorized_agencies = []
    with pytest.raises(HTTPException, match="no authorized destination"):
        authorize_partner_destination(source, 12)
