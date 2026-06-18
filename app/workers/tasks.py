import uuid

import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories.job_repository import JobRepository
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.healthcheck")
def healthcheck() -> str:
    """Infrastructure-only task used to verify worker registration."""

    return "ok"


@celery_app.task(name="app.workers.tasks.process_transaction_job")
def process_transaction_job(job_id: str) -> None:
    """Run CSV ingestion and cleaning for an uploaded transaction job."""

    parsed_job_id = uuid.UUID(job_id)

    db = SessionLocal()
    repository = JobRepository(db)
    try:
        job = repository.update_status(job_id=parsed_job_id, status="processing")
        if job is None:
            raise ValueError(f"Job {job_id} was not found.")
        db.commit()

        PipelineService(db).process_job(parsed_job_id)

        repository.update_status(job_id=parsed_job_id, status="completed")
        db.commit()
        logger.info("Job completed", extra={"job_id": job_id})
    except Exception as exc:
        db.rollback()
        repository.update_status(
            job_id=parsed_job_id,
            status="failed",
            error_message=str(exc),
        )
        db.commit()
        logger.exception("Job failed", extra={"job_id": job_id})
        raise
    finally:
        db.close()
