from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.user import User
from security.auth import get_current_user, require_role
from services.activity_service import create_activity_log


router = APIRouter(prefix="/integrations", tags=["Integrations"])


class IntegrationSourceCreate(BaseModel):
    name: str
    source_type: str
    api_url: Optional[str] = None
    description: Optional[str] = None


class IntegrationSourceUpdate(BaseModel):
    status: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/")
def create_integration_source(
    data: IntegrationSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    allowed_source_types = {
        "hospital",
        "transportation",
        "camera",
        "toll",
        "cell_provider",
        "social_media",
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
        status="pending",
        is_active=False,
    )

    db.add(source)
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

    return source


@router.get("/")
def get_integration_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(IntegrationSource).order_by(IntegrationSource.created_at.desc()).all()


@router.put("/{source_id}")
def update_integration_source(
    source_id: int,
    data: IntegrationSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
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

    return source
