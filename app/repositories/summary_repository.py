import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_summary import JobSummary


class SummaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_id(self, job_id: uuid.UUID) -> JobSummary | None:
        statement = select(JobSummary).where(JobSummary.job_id == job_id)
        return self.db.scalars(statement).one_or_none()

    def upsert(
        self,
        *,
        job_id: uuid.UUID,
        total_spend_inr: Decimal,
        total_spend_usd: Decimal,
        top_merchants: list[dict[str, Any]],
        category_breakdown: dict[str, Any],
        anomaly_count: int,
        narrative: str | None,
        risk_level: str | None,
    ) -> JobSummary:
        summary = self.get_by_job_id(job_id)
        if summary is None:
            summary = JobSummary(job_id=job_id)
            self.db.add(summary)

        summary.total_spend_inr = total_spend_inr
        summary.total_spend_usd = total_spend_usd
        summary.top_merchants = top_merchants
        summary.category_breakdown = category_breakdown
        summary.anomaly_count = anomaly_count
        summary.narrative = narrative
        summary.risk_level = risk_level
        self.db.flush()
        self.db.refresh(summary)
        return summary
