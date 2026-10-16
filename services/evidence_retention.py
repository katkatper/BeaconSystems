from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException

from services.clock import utc_now


@dataclass(frozen=True)
class RetentionDecision:
    eligible: bool
    reason: str


def retention_decision(evidence, now: datetime | None = None) -> RetentionDecision:
    effective_now = now or utc_now()
    if evidence.legal_hold:
        return RetentionDecision(False, "legal_hold")
    if evidence.disposition_status != "active":
        return RetentionDecision(False, "already_dispositioned")
    if evidence.retention_until is None:
        return RetentionDecision(False, "retention_not_scheduled")
    if evidence.retention_until > effective_now:
        return RetentionDecision(False, "retention_period_active")
    return RetentionDecision(True, "retention_period_complete")


def assert_evidence_disposition_allowed(evidence, now: datetime | None = None) -> None:
    decision = retention_decision(evidence, now)
    if not decision.eligible:
        raise HTTPException(
            status_code=409,
            detail="Evidence is not eligible for disposition",
        )
