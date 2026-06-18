import csv
import io
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.job_repository import JobRepository
from app.repositories.summary_repository import SummaryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.job import (
    JobListItem,
    JobResultsResponse,
    JobStatus,
    JobStatusResponse,
    JobUploadResponse,
)
from app.schemas.transaction import TransactionResponse
from app.utils.file_storage import FileStorage
from app.workers.tasks import process_transaction_job


class InvalidUploadError(ValueError):
    pass


class JobNotFoundError(LookupError):
    pass


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.job_repository = JobRepository(db)
        self.summary_repository = SummaryRepository(db)
        self.transaction_repository = TransactionRepository(db)
        self.storage = FileStorage(get_settings().upload_dir)

    def create_upload_job(self, upload: UploadFile) -> JobUploadResponse:
        filename = Path(upload.filename or "").name
        if not filename.lower().endswith(".csv"):
            raise InvalidUploadError("Only .csv files are supported.")

        content = self._read_upload(upload)
        row_count_raw = self._count_csv_rows(content)
        job_id = uuid.uuid4()

        self.storage.save_job_upload(job_id=job_id, content=content)
        job = self.job_repository.create(
            job_id=job_id,
            filename=filename,
            status=JobStatus.pending.value,
            row_count_raw=row_count_raw,
        )
        self.db.commit()
        process_transaction_job.delay(str(job.id))
        return JobUploadResponse(job_id=job.id, status=JobStatus.pending)

    def list_jobs(self, *, status: JobStatus | None = None) -> list[JobListItem]:
        jobs = self.job_repository.list(status=status.value if status else None)
        return [JobListItem.model_validate(job) for job in jobs]

    def get_job_status(self, job_id: uuid.UUID) -> JobStatusResponse:
        job = self.job_repository.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} was not found.")

        summary = None
        if job.status == JobStatus.completed.value:
            summary = self.summary_repository.get_by_job_id(job_id)

        return JobStatusResponse(
            job_id=job.id,
            status=JobStatus(job.status),
            created_at=job.created_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            summary=summary,
        )

    def get_job_results(self, job_id: uuid.UUID) -> JobResultsResponse:
        job = self.job_repository.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} was not found.")

        summary = self.summary_repository.get_by_job_id(job_id)
        transactions = self.transaction_repository.list_by_job_id(job_id)
        anomalies = self.transaction_repository.list_anomalies_by_job_id(job_id)

        return JobResultsResponse(
            job=JobListItem.model_validate(job),
            summary=summary,
            anomalies=[
                TransactionResponse.model_validate(transaction)
                for transaction in anomalies
            ],
            category_breakdown=summary.category_breakdown if summary else {},
            transactions=[
                TransactionResponse.model_validate(transaction)
                for transaction in transactions
            ],
        )

    def _read_upload(self, upload: UploadFile) -> bytes:
        content = upload.file.read()
        if not content or not content.strip():
            raise InvalidUploadError("Uploaded CSV file is empty.")
        return content

    def _count_csv_rows(self, content: bytes) -> int:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InvalidUploadError("Uploaded CSV must be UTF-8 encoded.") from exc

        rows = list(csv.reader(io.StringIO(text)))
        if not rows:
            raise InvalidUploadError("Uploaded CSV file is empty.")

        return max(len(rows) - 1, 0)
