from datetime import date, datetime


SUPPORTED_DATE_FORMATS = ("%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d")


def parse_transaction_date(value: str) -> date:
    normalized = value.strip()
    for date_format in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Unsupported date format: {value}")
