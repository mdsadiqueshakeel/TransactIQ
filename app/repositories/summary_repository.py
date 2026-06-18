import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_summary import JobSummary


class SummaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_id(self, job_id: uuid.UUID) -> JobSummary | None:
        statement = select(JobSummary).where(JobSummary.job_id == job_id)
        return self.db.scalars(statement).one_or_none()
