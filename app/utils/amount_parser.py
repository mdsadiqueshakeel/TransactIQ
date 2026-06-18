from decimal import Decimal, InvalidOperation


def parse_transaction_amount(value: str) -> Decimal:
    normalized = value.strip().replace("$", "").replace(",", "")
    if not normalized:
        raise ValueError("Amount cannot be empty.")

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount value: {value}") from exc
