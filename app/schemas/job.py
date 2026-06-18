from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.summary import JobSummaryResponse
from app.schemas.transaction import TransactionResponse


class JobStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobUploadResponse(BaseModel):
    job_id: UUID = Field(examples=["f4b59725-4480-48e8-a91f-3981c8315fdb"])
    status: JobStatus = Field(examples=["pending"])


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(examples=["f4b59725-4480-48e8-a91f-3981c8315fdb"])
    filename: str = Field(examples=["transactions.csv"])
    status: JobStatus = Field(examples=["completed"])
    row_count_raw: int = Field(examples=[95])
    row_count_clean: int = Field(examples=[85])
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: UUID = Field(examples=["f4b59725-4480-48e8-a91f-3981c8315fdb"])
    status: JobStatus = Field(examples=["completed"])
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None = Field(default=None, examples=[None])
    summary: JobSummaryResponse | None = None


class JobResultsResponse(BaseModel):
    job: JobListItem
    summary: JobSummaryResponse | None
    anomalies: list[TransactionResponse]
    category_breakdown: dict
    transactions: list[TransactionResponse]
