from collections import defaultdict
import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.repositories.summary_repository import SummaryRepository
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, db: Session) -> None:
        self.summary_repository = SummaryRepository(db)
        self.gemini_service = GeminiService()

    def generate_and_store(
        self,
        *,
        job_id: UUID,
        transactions: list[Transaction],
    ) -> bool:
        aggregates = self._compute_aggregates(transactions)
        llm_failed = False
        narrative = None
        risk_level = "medium"

        try:
            narrative, risk_level = self.gemini_service.generate_summary_narrative(
                aggregates
            )
        except Exception as exc:
            logger.exception(
                "Gemini summary generation failed",
                extra={
                    "job_id": str(job_id),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            llm_failed = True
            narrative = "Spending summary narrative is unavailable."

        self.summary_repository.upsert(
            job_id=job_id,
            total_spend_inr=aggregates["total_spend_inr"],
            total_spend_usd=aggregates["total_spend_usd"],
            top_merchants=aggregates["top_merchants"],
            category_breakdown=aggregates["category_breakdown"],
            anomaly_count=aggregates["anomaly_count"],
            narrative=narrative,
            risk_level=risk_level,
        )
        return llm_failed

    def _compute_aggregates(
        self,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        spend_by_currency = defaultdict(Decimal)
        spend_by_merchant = defaultdict(Decimal)
        spend_by_category = defaultdict(Decimal)
        anomaly_count = 0

        for transaction in transactions:
            spend_by_currency[transaction.currency] += transaction.amount
            spend_by_merchant[transaction.merchant] += transaction.amount
            spend_by_category[transaction.final_category] += transaction.amount
            if transaction.is_anomaly:
                anomaly_count += 1

        top_merchants = [
            {"merchant": merchant, "total": str(total)}
            for merchant, total in sorted(
                spend_by_merchant.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:3]
        ]

        return {
            "total_spend_inr": spend_by_currency["INR"],
            "total_spend_usd": spend_by_currency["USD"],
            "top_merchants": top_merchants,
            "category_breakdown": {
                category: str(total) for category, total in spend_by_category.items()
            },
            "anomaly_count": anomaly_count,
        }
