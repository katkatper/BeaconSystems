from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.agencies import Agencies
from models.async_job import AsyncJob
from models.case import Cases
from models.evidence import Evidence
from models.partner_intake_record import PartnerIntakeRecord


@dataclass(frozen=True)
class UsageMetric:
    used: int
    quota: int | None

    def as_dict(self) -> dict:
        remaining = max(0, self.quota - self.used) if self.quota is not None else None
        return {
            "used": self.used,
            "quota": self.quota,
            "remaining": remaining,
            "percent_used": (
                round((self.used / self.quota) * 100, 2)
                if self.quota
                else None
            ),
            "exceeded": self.quota is not None and self.used >= self.quota,
        }


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def agency_storage_bytes(db: Session, agency_id: int) -> int:
    value = (
        db.query(func.coalesce(func.sum(Evidence.file_size_bytes), 0))
        .join(Cases, Cases.case_id == Evidence.case_id)
        .filter(Cases.agency_id == agency_id)
        .scalar()
    )
    return int(value or 0)


def agency_capacity_usage(db: Session, agency: Agencies, now: datetime) -> dict:
    month_start = _month_start(now)
    storage_bytes = agency_storage_bytes(db, agency.agency_id)
    provider_requests = (
        db.query(func.count(PartnerIntakeRecord.intake_id))
        .filter(
            PartnerIntakeRecord.agency_id == agency.agency_id,
            PartnerIntakeRecord.received_at >= month_start,
        )
        .scalar()
    )
    jobs = (
        db.query(func.count(AsyncJob.job_id))
        .filter(
            AsyncJob.agency_id == agency.agency_id,
            AsyncJob.created_at >= month_start,
        )
        .scalar()
    )
    return {
        "agency_id": agency.agency_id,
        "period_start": month_start,
        "storage_bytes": UsageMetric(
            int(storage_bytes or 0), agency.storage_quota_bytes
        ).as_dict(),
        "provider_requests": UsageMetric(
            int(provider_requests or 0), agency.monthly_provider_request_quota
        ).as_dict(),
        "jobs": UsageMetric(int(jobs or 0), agency.monthly_job_quota).as_dict(),
    }
