from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.person import Person
from models.user import User
from security.auth import get_current_user, require_role
from schemas.person_schema import PersonCreate, PersonUpdate, PersonResponse, MessageResponse


router = APIRouter(prefix="/persons", tags=["Persons"])


@router.get("/test")
def persons_test():
    return {"message": "Persons router is working"}


@router.get("/", response_model=List[PersonResponse])
def get_persons(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Person)

    if status:
        query = query.filter(Person.status == status)

    if risk_level:
        query = query.filter(Person.risk_level == risk_level)

    return query.offset(offset).limit(limit).all()


@router.get("/{person_id}", response_model=PersonResponse)
def get_person_by_id(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return person


@router.post("/", response_model=MessageResponse)
def create_person(
    data: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "investigator")),
):
    new_person = Person(**data.model_dump())

    db.add(new_person)
    db.commit()
    db.refresh(new_person)

    return {
        "message": "Person created",
        "person_id": new_person.person_id,
    }


@router.put("/{person_id}", response_model=MessageResponse)
def update_person(
    person_id: int,
    data: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "investigator")),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)

    return {"message": "Person updated"}


@router.delete("/{person_id}", response_model=MessageResponse)
def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    db.delete(person)
    db.commit()

    return {"message": "Person deleted"}