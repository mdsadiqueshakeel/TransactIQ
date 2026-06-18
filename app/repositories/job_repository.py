import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        job_id: uuid.UUID,
        filename: str,
        status: str,
        row_count_raw: int,
    ) -> Job:
        job = Job(
            id=job_id,
            filename=filename,
            status=status,
            row_count_raw=row_count_raw,
            row_count_clean=0,
        )
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        return self.db.get(Job, job_id)

    def list(self, *, status: str | None = None) -> list[Job]:
        statement = select(Job).order_by(Job.created_at.desc())
        if status is not None:
            statement = statement.where(Job.status == status)
        return list(self.db.scalars(statement).all())

    def update_status(
        self,
        *,
        job_id: uuid.UUID,
        status: str,
        error_message: str | None = None,
    ) -> Job | None:
        job = self.get_by_id(job_id)
        if job is None:
            return None

        job.status = status
        job.error_message = error_message
        if status == "completed":
            job.completed_at = datetime.now(timezone.utc)
        elif status in {"pending", "processing"}:
            job.completed_at = None

        self.db.flush()
        self.db.refresh(job)
        return job

    def update_row_counts(
        self,
        *,
        job_id: uuid.UUID,
        row_count_raw: int | None = None,
        row_count_clean: int | None = None,
    ) -> Job | None:
        job = self.get_by_id(job_id)
        if job is None:
            return None

        if row_count_raw is not None:
            job.row_count_raw = row_count_raw
        if row_count_clean is not None:
            job.row_count_clean = row_count_clean

        self.db.flush()
        self.db.refresh(job)
        return job

    def mark_llm_failed(self, job_id: uuid.UUID) -> Job | None:
        job = self.get_by_id(job_id)
        if job is None:
            return None

        job.llm_failed = True
        self.db.flush()
        self.db.refresh(job)
        return job
