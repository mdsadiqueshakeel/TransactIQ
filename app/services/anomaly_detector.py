from collections import defaultdict
from decimal import Decimal
from statistics import median
from uuid import UUID

from app.models.transaction import Transaction


DOMESTIC_MERCHANTS = {"swiggy", "ola", "irctc"}
HIGH_AMOUNT_ACCOUNT_MEDIAN = "HIGH_AMOUNT_ACCOUNT_MEDIAN"
USD_DOMESTIC_MERCHANT = "USD_DOMESTIC_MERCHANT"


class AnomalyDetector:
    def detect(self, transactions: list[Transaction]) -> list[tuple[UUID, str]]:
        amounts_by_account: dict[str, list[Decimal]] = defaultdict(list)
        for transaction in transactions:
            amounts_by_account[transaction.account_id].append(transaction.amount)

        medians_by_account = {
            account_id: Decimal(str(median(amounts)))
            for account_id, amounts in amounts_by_account.items()
            if amounts
        }

        anomalies: list[tuple[UUID, str]] = []
        for transaction in transactions:
            median_amount = medians_by_account.get(transaction.account_id)
            if median_amount is not None and transaction.amount > median_amount * 3:
                anomalies.append((transaction.id, HIGH_AMOUNT_ACCOUNT_MEDIAN))
                continue

            if (
                transaction.currency == "USD"
                and transaction.merchant.strip().lower() in DOMESTIC_MERCHANTS
            ):
                anomalies.append((transaction.id, USD_DOMESTIC_MERCHANT))

        return anomalies
