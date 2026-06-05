from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.case_team_member import CaseTeamMember
from models.user import User


# Case access is the core "need-to-know" boundary for Beacon. Investigators see
# lead-assigned cases, active case-team memberships, and active grants.
# Supervisors see agency cases; admins see all.
def apply_case_access_filter(query, current_user: User, include_grants: bool = True):
    if current_user.role == "admin":
        return query

    if current_user.role == "agency_admin":
        return query.filter(Cases.agency_id == current_user.agency_id)

    if current_user.role == "investigator":
        filters = [Cases.investigator_id == current_user.user_id]

        team_case_ids = query.session.query(CaseTeamMember.case_id).filter(
            CaseTeamMember.user_id == current_user.user_id,
            CaseTeamMember.status == "active",
        )
        filters.append(Cases.case_id.in_(team_case_ids))

        if include_grants:
            granted_case_ids = query.session.query(CaseAccessGrant.case_id).filter(
                CaseAccessGrant.user_id == current_user.user_id,
                CaseAccessGrant.status == "active",
                or_(
                    CaseAccessGrant.expires_at.is_(None),
                    CaseAccessGrant.expires_at > datetime.utcnow(),
                ),
            )
            filters.append(Cases.case_id.in_(granted_case_ids))

        return query.filter(Cases.agency_id == current_user.agency_id).filter(
            or_(*filters)
        )

    return query.filter(Cases.case_id == -1)


def accessible_case_ids(
    db: Session,
    current_user: User,
    include_grants: bool = True,
) -> list[int]:
    query = apply_case_access_filter(db.query(Cases.case_id), current_user, include_grants)
    return [case_id for (case_id,) in query.all()]


def get_authorized_case(
    db: Session,
    case_id: int,
    current_user: User,
    include_grants: bool = True,
):
    query = db.query(Cases).filter(Cases.case_id == case_id)
    case = apply_case_access_filter(query, current_user, include_grants).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    return case


def assert_case_write_access(db: Session, case_id: int, current_user: User):
    # Temporary case grants allow viewing only. Editing, uploading, and creating
    # linked records still require assignment or supervisor/admin authority.
    return get_authorized_case(
        db=db,
        case_id=case_id,
        current_user=current_user,
        include_grants=False,
    )


def apply_related_case_access_filter(
    query,
    case_id_column,
    current_user: User,
    include_grants: bool = True,
):
    if current_user.role == "admin":
        return query

    case_ids = accessible_case_ids(
        db=query.session,
        current_user=current_user,
        include_grants=include_grants,
    )

    if not case_ids:
        return query.filter(case_id_column == -1)

    return query.filter(case_id_column.in_(case_ids))
