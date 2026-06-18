from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    total_spend_inr: Decimal
    total_spend_usd: Decimal
    top_merchants: list[dict[str, Any]]
    category_breakdown: dict[str, Any]
    anomaly_count: int
    narrative: str | None
    risk_level: str | None
    created_at: datetime
