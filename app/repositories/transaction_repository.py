import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def delete_by_job_id(self, job_id: uuid.UUID) -> None:
        self.db.execute(delete(Transaction).where(Transaction.job_id == job_id))
        self.db.flush()

    def bulk_insert(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return

        rows_with_ids = [{"id": uuid.uuid4(), **row} for row in rows]
        self.db.bulk_insert_mappings(Transaction, rows_with_ids)
        self.db.flush()

    def list_by_job_id(self, job_id: uuid.UUID) -> list[Transaction]:
        statement = (
            select(Transaction)
            .where(Transaction.job_id == job_id)
            .order_by(Transaction.created_at, Transaction.id)
        )
        return list(self.db.scalars(statement).all())

    def list_missing_category_by_job_id(self, job_id: uuid.UUID) -> list[Transaction]:
        statement = select(Transaction).where(
            Transaction.job_id == job_id,
            Transaction.original_category.is_(None),
        )
        return list(self.db.scalars(statement).all())

    def list_anomalies_by_job_id(self, job_id: uuid.UUID) -> list[Transaction]:
        statement = select(Transaction).where(
            Transaction.job_id == job_id,
            Transaction.is_anomaly.is_(True),
        )
        return list(self.db.scalars(statement).all())

    def update_anomalies(
        self,
        updates: list[tuple[uuid.UUID, str]],
    ) -> None:
        transactions = [self.db.get(Transaction, transaction_id) for transaction_id, _ in updates]
        reasons_by_id = dict(updates)
        for transaction in transactions:
            if transaction is None:
                continue
            transaction.is_anomaly = True
            transaction.anomaly_reason = reasons_by_id[transaction.id]
        self.db.flush()

    def update_categories(
        self,
        updates: list[dict[str, Any]],
    ) -> None:
        for update in updates:
            transaction = self.db.get(Transaction, update["id"])
            if transaction is None:
                continue
            transaction.final_category = update["final_category"]
            transaction.llm_raw_response = update.get("llm_raw_response")
            transaction.llm_failed = update.get("llm_failed", False)
        self.db.flush()
