import logging
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.job_repository import JobRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.anomaly_detector import AnomalyDetector
from app.services.csv_cleaner import CsvCleaner
from app.services.gemini_service import GeminiService
from app.services.summary_service import SummaryService

logger = logging.getLogger(__name__)

CATEGORY_BATCH_SIZE = 25


class PipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.cleaner = CsvCleaner()
        self.anomaly_detector = AnomalyDetector()
        self.gemini_service = GeminiService()
        self.job_repository = JobRepository(db)
        self.transaction_repository = TransactionRepository(db)
        self.summary_service = SummaryService(db)

    def process_job(self, job_id: uuid.UUID) -> None:
        csv_path = self._get_upload_path(job_id)
        dataframe = self._load_csv(csv_path)
        row_count_raw = len(dataframe)

        logger.info(
            "CSV loaded",
            extra={
                "job_id": str(job_id),
                "file_path": str(csv_path),
                "row_count_raw": row_count_raw,
            },
        )

        cleaned_rows, duplicates_removed = self.cleaner.clean(dataframe)
        logger.info(
            "Duplicates removed",
            extra={
                "job_id": str(job_id),
                "duplicates_removed": duplicates_removed,
            },
        )

        transaction_rows = self._attach_job_ids(job_id, cleaned_rows)
        self.transaction_repository.delete_by_job_id(job_id)
        self.transaction_repository.bulk_insert(transaction_rows)

        row_count_clean = len(transaction_rows)
        self.job_repository.update_row_counts(
            job_id=job_id,
            row_count_raw=row_count_raw,
            row_count_clean=row_count_clean,
        )

        logger.info(
            "Rows persisted",
            extra={
                "job_id": str(job_id),
                "row_count_clean": row_count_clean,
            },
        )

        transactions = self.transaction_repository.list_by_job_id(job_id)
        anomaly_updates = self.anomaly_detector.detect(transactions)
        self.transaction_repository.update_anomalies(anomaly_updates)
        logger.info(
            "Anomalies stored",
            extra={
                "job_id": str(job_id),
                "anomaly_count": len(anomaly_updates),
            },
        )

        classification_failed = self._classify_missing_categories(job_id)
        transactions = self.transaction_repository.list_by_job_id(job_id)
        summary_failed = self.summary_service.generate_and_store(
            job_id=job_id,
            transactions=transactions,
        )
        if classification_failed or summary_failed:
            self.job_repository.mark_llm_failed(job_id)

        logger.info(
            "Summary created",
            extra={
                "job_id": str(job_id),
                "llm_failed": classification_failed or summary_failed,
            },
        )

    def _get_upload_path(self, job_id: uuid.UUID) -> Path:
        csv_path = self.settings.upload_dir / f"{job_id}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Uploaded CSV not found for job {job_id}")
        return csv_path

    def _load_csv(self, csv_path: Path) -> pd.DataFrame:
        return pd.read_csv(csv_path, dtype=str)

    def _attach_job_ids(
        self,
        job_id: uuid.UUID,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [{"job_id": job_id, **row} for row in rows]

    def _classify_missing_categories(self, job_id: uuid.UUID) -> bool:
        transactions = self.transaction_repository.list_missing_category_by_job_id(job_id)
        llm_failed = False

        for index in range(0, len(transactions), CATEGORY_BATCH_SIZE):
            batch = transactions[index : index + CATEGORY_BATCH_SIZE]
            payload = [
                {
                    "id": str(transaction.id),
                    "merchant": transaction.merchant,
                    "notes": transaction.notes,
                }
                for transaction in batch
            ]

            try:
                categories, raw_response = self.gemini_service.classify_categories(
                    payload
                )
                updates = [
                    {
                        "id": transaction.id,
                        "final_category": categories.get(str(transaction.id), "Other"),
                        "llm_raw_response": raw_response,
                        "llm_failed": False,
                    }
                    for transaction in batch
                ]
            except Exception as exc:
                logger.exception(
                    "Gemini category classification failed",
                    extra={
                        "job_id": str(job_id),
                        "batch_size": len(batch),
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                )
                llm_failed = True
                updates = [
                    {
                        "id": transaction.id,
                        "final_category": transaction.final_category,
                        "llm_raw_response": str(exc),
                        "llm_failed": True,
                    }
                    for transaction in batch
                ]

            self.transaction_repository.update_categories(updates)

        logger.info(
            "Categories classified",
            extra={
                "job_id": str(job_id),
                "missing_category_count": len(transactions),
                "llm_failed": llm_failed,
            },
        )
        return llm_failed
