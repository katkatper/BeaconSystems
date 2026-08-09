from models.case import Cases
from models.partner_intake_record import PartnerIntakeRecord
from models.person import Person
from models.user import User


def apply_person_agency_scope(query, current_user: User):
    """Restrict person records to cases owned by the caller's agency."""
    if current_user.role == "admin":
        return query

    return query.filter(
        Person.cases.any(Cases.agency_id == current_user.agency_id)
    )


def apply_partner_intake_agency_scope(query, current_user: User):
    """Restrict partner intake records to their explicit tenant owner."""
    if current_user.role == "admin":
        return query

    return query.filter(PartnerIntakeRecord.agency_id == current_user.agency_id)
