from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.agencies import Agencies
from models.integration_source import IntegrationSource
from models.integration_source_agency import IntegrationSourceAgency
from models.user import User
from security.auth import get_current_user, require_role
from security.partner_tokens import hash_partner_token
from services.activity_service import create_activity_log
from services.pagination import PaginationParams, paginate_query

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class IntegrationSourceCreate(BaseModel):
    name: str
    source_type: str
    api_url: Optional[str] = None
    description: Optional[str] = None
    adapter_key: str = "canonical_v1"
    field_mapping: dict[str, str] | None = None
    allowed_record_types: list[str] | None = None
    authorized_agency_ids: list[int] | None = None
    match_threshold: int = 60
    webhook_token: str | None = None


class IntegrationSourceUpdate(BaseModel):
    status: Optional[str] = None
    is_active: Optional[bool] = None
    adapter_key: Optional[str] = None
    field_mapping: dict[str, str] | None = None
    allowed_record_types: list[str] | None = None
    authorized_agency_ids: list[int] | None = None
    match_threshold: Optional[int] = None
    webhook_token: str | None = None


def serialize_integration_source(source: IntegrationSource) -> dict:
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "status": source.status,
        "is_active": source.is_active,
        "api_url": source.api_url,
        "description": source.description,
        "adapter_key": source.adapter_key,
        "field_mapping": source.field_mapping,
        "allowed_record_types": source.allowed_record_types,
        "authorized_agency_ids": sorted(
            item.agency_id for item in source.authorized_agencies
        ),
        "match_threshold": source.match_threshold,
        "webhook_configured": bool(source.webhook_secret_hash),
        "created_at": source.created_at,
    }


def validate_webhook_token(token: str | None) -> str | None:
    if token is None:
        return None
    if len(token) < 32:
        raise HTTPException(status_code=400, detail="Partner webhook token must be at least 32 characters")
    return hash_partner_token(token)


def replace_authorized_agencies(
    db: Session,
    source: IntegrationSource,
    agency_ids: list[int] | None,
) -> None:
    if agency_ids is None:
        return
    normalized_ids = sorted(set(agency_ids))
    found_ids = (
        {
            agency_id
            for (agency_id,) in db.query(Agencies.agency_id)
            .filter(Agencies.agency_id.in_(normalized_ids))
            .all()
        }
        if normalized_ids
        else set()
    )
    missing_ids = set(normalized_ids).difference(found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown authorized agency IDs: {', '.join(map(str, sorted(missing_ids)))}",
        )
    source.authorized_agencies = [
        IntegrationSourceAgency(agency_id=agency_id)
        for agency_id in normalized_ids
    ]


@router.post("/")
def create_integration_source(
    data: IntegrationSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    allowed_source_types = {
        "hospital",
        "medical_examiner",
        "crime_lab",
        "transportation",
        "camera",
        "toll",
        "cell_provider",
        "social_media",
        "fusion_center",
        "prosecutor",
        "court",
        "social_services",
        "family_portal",
        "ngo",
        "other",
    }

    if data.source_type not in allowed_source_types:
        raise HTTPException(status_code=400, detail="Invalid source type")

    source = IntegrationSource(
        name=data.name,
        source_type=data.source_type,
        api_url=data.api_url,
        description=data.description,
        adapter_key=data.adapter_key,
        field_mapping=data.field_mapping,
        allowed_record_types=data.allowed_record_types,
        match_threshold=max(1, min(data.match_threshold, 100)),
        webhook_secret_hash=validate_webhook_token(data.webhook_token),
        status="pending",
        is_active=False,
    )

    db.add(source)
    replace_authorized_agencies(db, source, data.authorized_agency_ids)
    db.commit()
    db.refresh(source)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CREATE_PARTNER_SOURCE",
        entity="integration_source",
        entity_id=source.id,
        details=f"Partner source created: {source.name}",
    )

    return serialize_integration_source(source)


@router.get("/")
def get_integration_sources(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(IntegrationSource)

    if current_user.role != "platform_admin":
        query = query.filter(
            IntegrationSource.status == "approved",
            IntegrationSource.is_active.is_(True),
            IntegrationSource.authorized_agencies.any(
                IntegrationSourceAgency.agency_id == current_user.agency_id
            ),
        )

    sources = paginate_query(
        query.order_by(IntegrationSource.created_at.desc()),
        pagination,
        response,
    )
    return [serialize_integration_source(source) for source in sources]


@router.put("/{source_id}")
def update_integration_source(
    source_id: int,
    data: IntegrationSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    allowed_statuses = {"pending", "approved", "denied", "suspended", "revoked"}

    source = db.query(IntegrationSource).filter(
        IntegrationSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Partner source not found")

    if data.status is not None:
        if data.status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")

        source.status = data.status

    if data.is_active is not None:
        source.is_active = data.is_active

    if data.adapter_key is not None:
        source.adapter_key = data.adapter_key
    if data.field_mapping is not None:
        source.field_mapping = data.field_mapping
    if data.allowed_record_types is not None:
        source.allowed_record_types = data.allowed_record_types
    replace_authorized_agencies(db, source, data.authorized_agency_ids)
    if data.match_threshold is not None:
        source.match_threshold = max(1, min(data.match_threshold, 100))
    if data.webhook_token is not None:
        source.webhook_secret_hash = validate_webhook_token(data.webhook_token)

    db.commit()
    db.refresh(source)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="UPDATE_PARTNER_SOURCE",
        entity="integration_source",
        entity_id=source.id,
        details=f"Partner source updated: {source.name}",
    )

    return serialize_integration_source(source)
