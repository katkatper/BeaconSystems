import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.person import Person
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import apply_case_access_filter
from schemas.case_schema import CaseCreate, CaseUpdate, CaseResponse, MessageResponse
from services.activity_service import create_activity_log


router = APIRouter(prefix="/cases", tags=["Cases"])


class CaseAccessCodeRequest(BaseModel):
    case_id: int
    access_code: str
    reason: str


class CaseAccessRequest(BaseModel):
    case_id: int
    reason_category: str
    reason: str


AUTO_APPROVED_REASON_CATEGORIES = {
    "assisting_investigator",
    "shift_coverage",
    "supervisor_directed",
    "linked_person_overlap",
    "emergency_field_support",
    "evidence_intake_support",
    "court_preparation",
}


def should_auto_approve_access(case: Cases, data: CaseAccessRequest, current_user: User):
    status = (case.case_status or "").lower()
    reason_category = data.reason_category.strip().lower()

    if current_user.role in {"admin", "agency_admin"}:
        return True

    if current_user.role != "investigator":
        return False

    if current_user.agency_id != case.agency_id:
        return False

    if status in {"closed", "archived"}:
        return False

    if reason_category not in AUTO_APPROVED_REASON_CATEGORIES:
        return False

    return len(data.reason.strip()) >= 20


def attach_case_list_display_fields(cases: list[Cases], db: Session):
    person_ids = {case.person_id for case in cases if case.person_id}
    investigator_ids = {case.investigator_id for case in cases if case.investigator_id}

    people = (
        {
            person.person_id: person
            for person in db.query(Person).filter(Person.person_id.in_(person_ids)).all()
        }
        if person_ids
        else {}
    )
    investigators = (
        {
            user.user_id: user
            for user in db.query(User).filter(User.user_id.in_(investigator_ids)).all()
        }
        if investigator_ids
        else {}
    )

    for case in cases:
        person = people.get(case.person_id)
        investigator = investigators.get(case.investigator_id)

        case.missing_person_last_name = person.last_name if person else None
        case.investigator_name = investigator.username if investigator else None

    return cases


@router.get("/by-person/{person_id}", response_model=List[CaseResponse])

def get_cases_by_person(

    person_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):


    query = db.query(Cases).filter(Cases.person_id == person_id)

    query = apply_case_access_filter(query, current_user)

    return attach_case_list_display_fields(query.all(), db)


@router.get("/test")

def get_cases_test():

    return [
        {"case_id": 1, "case_number": "B-1001", "case_status": "Open"},

        {"case_id": 2, "case_number": "B-1002", "case_status": "Investigating"},
    ]



@router.get("/", response_model=List[CaseResponse])

def get_cases(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

    case_status: Optional[str] = Query(None),

    priority_level: Optional[str] = Query(None),

    investigator_id: Optional[int] = Query(None),

    include_archived: bool = Query(False),

    limit: int = Query(20, ge=1, le=100),

    offset: int = Query(0, ge=0),
):

    query = db.query(Cases)

    query = apply_case_access_filter(query, current_user)

    if not include_archived:
        query = query.filter(Cases.case_status != "archived")

    if case_status:
        query = query.filter(Cases.case_status == case_status)

    if priority_level:
        query = query.filter(Cases.priority_level == priority_level)

    if investigator_id is not None:
        query = query.filter(Cases.investigator_id == investigator_id)

    cases = query.offset(offset).limit(limit).all()
    attach_case_list_display_fields(cases, db)

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="VIEW_CASES",

        entity="case",

        details=f"{current_user.username} viewed accessible cases",
    )

    return cases


@router.post("/", response_model=CaseResponse)

def create_case(

    case: CaseCreate,

    request: Request,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    new_case = Cases(**case.model_dump())

    if current_user.role != "admin":

        new_case.agency_id = current_user.agency_id

    if not new_case.investigator_id:

        new_case.investigator_id = current_user.user_id

    db.add(new_case)
    db.commit()
    db.refresh(new_case)


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="CREATE_CASE",

        entity="case",

        entity_id=new_case.case_id,

        details=f"Case created: {new_case.title}",

        ip_address=request.client.host if request.client else None,
    )

    return new_case



@router.get("/{case_id}", response_model=CaseResponse)

def get_case_by_id(

    case_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):


    query = db.query(Cases).filter(Cases.case_id == case_id)

    query = apply_case_access_filter(query, current_user)

    case = query.first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    return case


@router.put("/{case_id}", response_model=MessageResponse)

def update_case(

    case_id: int,

    data: CaseUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):


    query = db.query(Cases).filter(Cases.case_id == case_id)

    query = apply_case_access_filter(query, current_user, include_grants=False)

    case = query.first()

    if not case:

        create_activity_log(

            db=db,

            user_id=current_user.user_id,

            agency_id=current_user.agency_id,

            action="UNAUTHORIZED_ACCESS",

            entity="case",

            entity_id=case_id,

            details=f"{current_user.username} tried to update restricted case",
        )
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = data.model_dump(exclude_unset=True)

    if current_user.role != "admin":

        update_data.pop("agency_id", None)

    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="UPDATE_CASE",

        entity="case",

        entity_id=case.case_id,

        details=f"Updated case {case.case_number}",
    )

    return {"message": "Case updated"}


@router.post("/access-code", response_model=MessageResponse)
def request_case_access_with_code(
    data: CaseAccessCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "agency_admin", "admin")),
):
    if len(data.reason.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="A specific access reason is required",
        )

    expected_code = os.getenv("BEACON_CASE_ACCESS_CODE", "BEACON-DEMO-CODE")

    if data.access_code != expected_code:
        create_activity_log(
            db=db,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            action="CASE_ACCESS_CODE_DENIED",
            entity="case",
            entity_id=data.case_id,
            details=f"{current_user.username} entered an invalid case access code",
        )
        raise HTTPException(status_code=403, detail="Invalid access code")

    case = db.query(Cases).filter(Cases.case_id == data.case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if current_user.role != "admin" and case.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Case belongs to another agency")

    existing_grant = db.query(CaseAccessGrant).filter(
        CaseAccessGrant.case_id == data.case_id,
        CaseAccessGrant.user_id == current_user.user_id,
        CaseAccessGrant.status == "active",
    ).first()

    if existing_grant:
        existing_grant.reason = data.reason
        db.commit()
        db.refresh(existing_grant)
    else:
        grant = CaseAccessGrant(
            case_id=data.case_id,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            reason=data.reason,
            status="active",
        )
        db.add(grant)
        db.commit()
        db.refresh(grant)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CASE_ACCESS_CODE_GRANTED",
        entity="case",
        entity_id=data.case_id,
        details=f"{current_user.username} accessed case by code. Reason: {data.reason}",
    )

    return {"message": "Case access granted and logged"}


@router.post("/access-request", response_model=MessageResponse)
def request_case_access(
    data: CaseAccessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("investigator", "agency_admin", "admin")),
):
    if len(data.reason.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="A specific access reason is required",
        )

    case = db.query(Cases).filter(Cases.case_id == data.case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    same_agency = current_user.role == "admin" or case.agency_id == current_user.agency_id

    if not same_agency:
        create_activity_log(
            db=db,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            action="CASE_ACCESS_REVIEW_REQUIRED",
            entity="case",
            entity_id=data.case_id,
            details=(
                f"{current_user.username} requested cross-agency access. "
                f"Category: {data.reason_category}. Reason: {data.reason}"
            ),
        )
        raise HTTPException(
            status_code=403,
            detail="Cross-agency access requires a formal partner/legal workflow",
        )

    auto_approved = should_auto_approve_access(case, data, current_user)
    status = "active" if auto_approved else "pending"
    approval_type = "auto" if auto_approved else "manual"
    expires_at = datetime.utcnow() + timedelta(hours=24) if auto_approved else None

    existing_grant = db.query(CaseAccessGrant).filter(
        CaseAccessGrant.case_id == data.case_id,
        CaseAccessGrant.user_id == current_user.user_id,
        CaseAccessGrant.status.in_(["active", "pending"]),
    ).first()

    if existing_grant:
        existing_grant.reason = data.reason
        existing_grant.reason_category = data.reason_category
        existing_grant.status = status
        existing_grant.approval_type = approval_type
        existing_grant.expires_at = expires_at
        existing_grant.revoked_at = None
        db.commit()
        db.refresh(existing_grant)
        grant = existing_grant
    else:
        grant = CaseAccessGrant(
            case_id=data.case_id,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            reason=data.reason,
            reason_category=data.reason_category,
            status=status,
            approval_type=approval_type,
            expires_at=expires_at,
        )
        db.add(grant)
        db.commit()
        db.refresh(grant)

    action = "CASE_ACCESS_AUTO_APPROVED" if auto_approved else "CASE_ACCESS_REVIEW_REQUIRED"

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action=action,
        entity="case",
        entity_id=data.case_id,
        details=(
            f"{current_user.username} requested case access. "
            f"Category: {data.reason_category}. Reason: {data.reason}"
        ),
    )

    if auto_approved:
        return {
            "message": "Case access auto-approved for 24 hours and logged",
        }

    return {
        "message": "Case access request submitted for supervisor review and logged",
    }


@router.put("/{case_id}/archive", response_model=MessageResponse)
def archive_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    query = db.query(Cases).filter(Cases.case_id == case_id)
    query = apply_case_access_filter(query, current_user, include_grants=False)

    case = query.first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    if (case.case_status or "").lower() != "closed":
        raise HTTPException(
            status_code=400,
            detail="Only closed cases can be archived",
        )

    case.case_status = "archived"

    db.commit()
    db.refresh(case)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="ARCHIVE_CASE",
        entity="case",
        entity_id=case.case_id,
        details=f"Archived case {case.case_number}",
    )

    return {"message": "Case archived"}


@router.delete("/{case_id}", response_model=MessageResponse)

def delete_case(

    case_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin")),
):

    query = db.query(Cases).filter(Cases.case_id == case_id)

    query = apply_case_access_filter(query, current_user, include_grants=False)

    case = query.first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    case_number = case.case_number

    case_id_value = case.case_id

    db.delete(case)
    db.commit()


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="DELETE_CASE",

        entity="case",

        entity_id=case_id_value,

        details=f"Deleted case {case_number}",
    )

    return {"message": "Case deleted"}


@router.get("/summary/counts", response_model=dict)

def get_case_counts(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):


    query = db.query(Cases)

    query = apply_case_access_filter(query, current_user)

    total = query.count()

    open_count = query.filter(Cases.case_status == "Open").count()

    closed_count = query.filter(Cases.case_status == "Closed").count()

    high_priority = query.filter(Cases.priority_level == "high").count()

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="VIEW_CASE_SUMMARY",

        entity="case",

        details=f"{current_user.username} viewed case summary counts",
    )

    return {
        "total": total,

        "open": open_count,

        "closed": closed_count,

        "high_priority": high_priority,
    }
