from celery import Celery

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.startup import validate_startup_configuration

settings = get_settings()
configure_logging()
validate_startup_configuration()

celery_app = Celery(
    "transactiq",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)
