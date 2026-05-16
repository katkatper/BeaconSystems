from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.case import Cases
from models.user import User
from security.auth import get_current_user, require_role
from schemas.case_schema import CaseCreate, CaseUpdate, CaseResponse, MessageResponse
from services.activity_service import create_activity_log


router = APIRouter(prefix="/cases", tags=["Cases"])


def apply_case_access_filter(query, current_user: User):

    if current_user.role == "admin":

        return query

    return query.filter(Cases.agency_id == current_user.agency_id)



@router.get("/by-person/{person_id}", response_model=List[CaseResponse])

def get_cases_by_person(

    person_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):


    query = db.query(Cases).filter(Cases.person_id == person_id)

    query = apply_case_access_filter(query, current_user)

    return query.all()


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

    limit: int = Query(20, ge=1, le=100),

    offset: int = Query(0, ge=0),
):

    query = db.query(Cases)

    query = apply_case_access_filter(query, current_user)

    if case_status:
        query = query.filter(Cases.case_status == case_status)

    if priority_level:
        query = query.filter(Cases.priority_level == priority_level)

    if investigator_id is not None:
        query = query.filter(Cases.investigator_id == investigator_id)

    cases = query.offset(offset).limit(limit).all()

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

    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
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

    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):


    query = db.query(Cases).filter(Cases.case_id == case_id)

    query = apply_case_access_filter(query, current_user)

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


@router.delete("/{case_id}", response_model=MessageResponse)

def delete_case(

    case_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin")),
):

    query = db.query(Cases).filter(Cases.case_id == case_id)

    query = apply_case_access_filter(query, current_user)

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