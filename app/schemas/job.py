from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.summary import JobSummaryResponse
from app.schemas.transaction import TransactionResponse


class JobStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobUploadResponse(BaseModel):
    job_id: UUID
    status: JobStatus


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    status: JobStatus
    row_count_raw: int
    row_count_clean: int
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None
    summary: JobSummaryResponse | None = None


class JobResultsResponse(BaseModel):
    job: JobListItem
    summary: JobSummaryResponse | None
    anomalies: list[TransactionResponse]
    category_breakdown: dict
    transactions: list[TransactionResponse]
