import time
import uuid

from sqlalchemy.exc import SQLAlchemyError

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories.job_repository import JobRepository


@celery_app.task(name="app.workers.tasks.healthcheck")
def healthcheck() -> str:
    """Infrastructure-only task used to verify worker registration."""

    return "ok"


@celery_app.task(name="app.workers.tasks.process_transaction_job")
def process_transaction_job(job_id: str) -> None:
    """Phase 2 placeholder to verify queue-driven job status transitions."""

    parsed_job_id = uuid.UUID(job_id)

    db = SessionLocal()
    repository = JobRepository(db)
    try:
        repository.update_status(job_id=parsed_job_id, status="processing")
        db.commit()

        time.sleep(5)

        repository.update_status(job_id=parsed_job_id, status="completed")
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        repository.update_status(
            job_id=parsed_job_id,
            status="failed",
            error_message=str(exc),
        )
        db.commit()
        raise
    finally:
        db.close()
