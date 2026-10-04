import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta

from config.settings import CASE_ACCESS_CODE
from models.case import Cases
from models.user import User
from services.clock import utc_now


AUTO_APPROVED_REASON_CATEGORIES = {
    "assisting_investigator",
    "shift_coverage",
    "supervisor_directed",
    "linked_person_overlap",
    "emergency_field_support",
    "evidence_intake_support",
    "court_preparation",
}


@dataclass(frozen=True)
class AccessDecision:
    auto_approved: bool
    status: str
    approval_type: str
    expires_at: datetime | None


def case_access_code_matches(provided_code: str) -> bool:
    """Compare the configured code without a built-in development fallback."""
    return bool(CASE_ACCESS_CODE) and hmac.compare_digest(
        provided_code.encode("utf-8"),
        CASE_ACCESS_CODE.encode("utf-8"),
    )


def should_auto_approve_access(
    case: Cases,
    current_user: User,
    *,
    reason_category: str,
    reason: str,
) -> bool:
    status = (case.case_status or "").lower()
    normalized_category = reason_category.strip().lower()

    if current_user.role in {"platform_admin", "agency_admin"}:
        return True
    if current_user.role != "investigator":
        return False
    if current_user.agency_id != case.agency_id:
        return False
    if status in {"closed", "archived"}:
        return False
    if normalized_category not in AUTO_APPROVED_REASON_CATEGORIES:
        return False
    return len(reason.strip()) >= 20


def decide_case_access(
    case: Cases,
    current_user: User,
    *,
    reason_category: str,
    reason: str,
    now: datetime | None = None,
) -> AccessDecision:
    auto_approved = should_auto_approve_access(
        case,
        current_user,
        reason_category=reason_category,
        reason=reason,
    )
    return AccessDecision(
        auto_approved=auto_approved,
        status="active" if auto_approved else "pending",
        approval_type="auto" if auto_approved else "manual",
        expires_at=(now or utc_now()) + timedelta(hours=24)
        if auto_approved
        else None,
    )
