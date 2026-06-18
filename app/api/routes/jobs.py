import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.job import (
    JobListItem,
    JobResultsResponse,
    JobStatus,
    JobStatusResponse,
    JobUploadResponse,
)
from app.services.job_service import InvalidUploadError, JobNotFoundError, JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

JOB_ID_EXAMPLE = "f4b59725-4480-48e8-a91f-3981c8315fdb"


@router.post(
    "/upload",
    response_model=JobUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload transaction CSV",
    description="Uploads a CSV file, creates a pending job, stores the file, and enqueues asynchronous processing.",
    response_description="Created job identifier and initial pending status.",
    responses={
        400: {"description": "Invalid, empty, or non-CSV upload."},
        500: {"description": "Job creation failed."},
        202: {
            "description": "CSV accepted and processing job queued.",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": JOB_ID_EXAMPLE,
                        "status": "pending",
                    }
                }
            },
        },
    },
)
def upload_job(
    file: UploadFile = File(
        ...,
        description="Upload the provided transactions.csv file.",
    ),
    db: Session = Depends(get_db),
) -> JobUploadResponse:
    service = JobService(db)
    try:
        return service.create_upload_job(file)
    except InvalidUploadError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create job.",
        ) from exc


@router.get(
    "",
    response_model=list[JobListItem],
    summary="List jobs",
    description="Lists all processing jobs and optionally filters them by status.",
    response_description="Jobs ordered by newest first.",
    responses={
        200: {
            "description": "Job list returned successfully.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": JOB_ID_EXAMPLE,
                            "filename": "transactions.csv",
                            "status": "completed",
                            "row_count_raw": 95,
                            "row_count_clean": 85,
                            "created_at": "2026-06-18T13:40:36.458092Z",
                        }
                    ]
                }
            },
        }
    },
)
def list_jobs(
    status_filter: JobStatus | None = Query(
        default=None,
        alias="status",
        description="Optional job status filter.",
        examples=["completed"],
    ),
    db: Session = Depends(get_db),
) -> list[JobListItem]:
    service = JobService(db)
    return service.list_jobs(status=status_filter)


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Returns the current status for a job and includes summary data when the job is completed.",
    response_description="Current job status and optional summary.",
    responses={
        200: {
            "description": "Job status returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": JOB_ID_EXAMPLE,
                        "status": "completed",
                        "created_at": "2026-06-18T13:40:36.458092Z",
                        "completed_at": "2026-06-18T13:41:02.120000Z",
                        "error_message": None,
                        "summary": None,
                    }
                }
            },
        },
        404: {"description": "Job not found."},
    },
)
def get_job_status(
    job_id: uuid.UUID = Path(
        ...,
        description="UUID returned by POST /jobs/upload.",
        examples=[JOB_ID_EXAMPLE],
    ),
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    service = JobService(db)
    try:
        return service.get_job_status(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{job_id}/results",
    response_model=JobResultsResponse,
    summary="Get job results",
    description="Returns cleaned transactions, anomalies, category breakdown, and summary for a job.",
    response_description="Full processed job output.",
    responses={
        200: {
            "description": "Full processed job results returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "job": {
                            "id": JOB_ID_EXAMPLE,
                            "filename": "transactions.csv",
                            "status": "completed",
                            "row_count_raw": 95,
                            "row_count_clean": 85,
                            "created_at": "2026-06-18T13:40:36.458092Z",
                        },
                        "summary": {
                            "id": "7f6a6f54-bc78-4f60-a216-a981a8a33d2d",
                            "job_id": JOB_ID_EXAMPLE,
                            "total_spend_inr": "248563.75",
                            "total_spend_usd": "1835.20",
                            "top_merchants": [{"merchant": "Flipkart", "total": "42123.50"}],
                            "category_breakdown": {"Food": "12345.50"},
                            "anomaly_count": 4,
                            "narrative": "Spending is concentrated across shopping and food.",
                            "risk_level": "medium",
                            "created_at": "2026-06-18T13:41:02.120000Z",
                        },
                        "anomalies": [],
                        "category_breakdown": {"Food": "12345.50"},
                        "transactions": [],
                    }
                }
            },
        },
        404: {"description": "Job not found."},
    },
)
def get_job_results(
    job_id: uuid.UUID = Path(
        ...,
        description="UUID returned by POST /jobs/upload.",
        examples=[JOB_ID_EXAMPLE],
    ),
    db: Session = Depends(get_db),
) -> JobResultsResponse:
    service = JobService(db)
    try:
        return service.get_job_results(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
