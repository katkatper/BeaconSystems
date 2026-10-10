"""Efficient aggregate metrics for the operational dashboard."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func

from models.case import Cases


@dataclass(frozen=True)
class CaseDashboardMetrics:
    total_cases: int
    open_cases: int
    high_priority_cases: int
    critical_cases: int
    high_risk_cases: int
    inactive_7_days: int
    inactive_14_days: int
    unassigned_cases: int


def load_case_dashboard_metrics(
    case_query,
    *,
    seven_days_ago: datetime,
    fourteen_days_ago: datetime,
    inactive_statuses: tuple[str, ...],
) -> CaseDashboardMetrics:
    """Load core tenant-scoped case counts in one database round trip."""
    normalized_status = func.lower(Cases.case_status)
    normalized_priority = func.lower(Cases.priority_level)
    is_active = normalized_status.notin_(inactive_statuses)

    def conditional_count(condition):
        return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)

    row = case_query.with_entities(
        func.count(Cases.case_id).label("total_cases"),
        conditional_count(normalized_status == "open").label("open_cases"),
        conditional_count(normalized_priority.in_(("high", "critical"))).label(
            "high_priority_cases"
        ),
        conditional_count(is_active & (normalized_priority == "critical")).label(
            "critical_cases"
        ),
        conditional_count(is_active & (normalized_priority == "high")).label(
            "high_risk_cases"
        ),
        conditional_count(is_active & (Cases.updated_at <= seven_days_ago)).label(
            "inactive_7_days"
        ),
        conditional_count(is_active & (Cases.updated_at <= fourteen_days_ago)).label(
            "inactive_14_days"
        ),
        conditional_count(is_active & Cases.investigator_id.is_(None)).label(
            "unassigned_cases"
        ),
    ).one()

    return CaseDashboardMetrics(
        **{
            field: int(getattr(row, field) or 0)
            for field in CaseDashboardMetrics.__dataclass_fields__
        }
    )
