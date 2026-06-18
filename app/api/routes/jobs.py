import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.job import JobListItem, JobStatus, JobStatusResponse, JobUploadResponse
from app.services.job_service import InvalidUploadError, JobNotFoundError, JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/upload",
    response_model=JobUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload transaction CSV",
    description="Uploads a CSV file, creates a pending job, stores the file, and enqueues asynchronous processing.",
)
def upload_job(
    file: UploadFile = File(...),
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
)
def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[JobListItem]:
    service = JobService(db)
    return service.list_jobs(status=status_filter)


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Returns the current status for a job and includes summary data when the job is completed.",
)
def get_job_status(
    job_id: uuid.UUID,
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
