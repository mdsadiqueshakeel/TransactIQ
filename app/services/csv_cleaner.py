from typing import Any

import pandas as pd

from app.utils.amount_parser import parse_transaction_amount
from app.utils.date_parser import parse_transaction_date


REQUIRED_COLUMNS = [
    "txn_id",
    "date",
    "merchant",
    "amount",
    "currency",
    "status",
    "category",
    "account_id",
    "notes",
]


class CsvValidationError(ValueError):
    pass


class CsvCleaner:
    def clean(self, dataframe: pd.DataFrame) -> tuple[list[dict[str, Any]], int]:
        self._validate_columns(dataframe)

        original_count = len(dataframe)
        cleaned_frame = dataframe[REQUIRED_COLUMNS].copy().drop_duplicates()
        duplicates_removed = original_count - len(cleaned_frame)

        rows: list[dict[str, Any]] = []
        for row_number, record in enumerate(
            cleaned_frame.to_dict(orient="records"), start=2
        ):
            rows.append(self._clean_record(record, row_number))

        return rows, duplicates_removed

    def _validate_columns(self, dataframe: pd.DataFrame) -> None:
        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in dataframe.columns
        ]
        if missing_columns:
            raise CsvValidationError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

    def _clean_record(self, record: dict[str, Any], row_number: int) -> dict[str, Any]:
        category = self._optional_string(record["category"])
        try:
            parsed_date = parse_transaction_date(
                self._required_string(record["date"], "date")
            )
            parsed_amount = parse_transaction_amount(
                self._required_string(record["amount"], "amount")
            )
        except ValueError as exc:
            raise CsvValidationError(f"Row {row_number}: {exc}") from exc

        return {
            "txn_id": self._optional_string(record["txn_id"]),
            "date": parsed_date,
            "merchant": self._required_string(record["merchant"], "merchant"),
            "amount": parsed_amount,
            "currency": self._required_string(record["currency"], "currency").upper(),
            "status": self._required_string(record["status"], "status").upper(),
            "original_category": category,
            "final_category": category if category is not None else "Uncategorised",
            "account_id": self._required_string(record["account_id"], "account_id"),
            "notes": self._optional_string(record["notes"]),
            "is_anomaly": False,
            "anomaly_reason": None,
            "llm_raw_response": None,
            "llm_failed": False,
        }

    def _optional_string(self, value: Any) -> str | None:
        if pd.isna(value):
            return None

        normalized = str(value).strip()
        return normalized or None

    def _required_string(self, value: Any, field_name: str) -> str:
        normalized = self._optional_string(value)
        if normalized is None:
            raise CsvValidationError(f"Missing required value for {field_name}")
        return normalized
