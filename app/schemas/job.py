from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.summary import JobSummaryResponse


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
