from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(examples=["7f6a6f54-bc78-4f60-a216-a981a8a33d2d"])
    job_id: UUID = Field(examples=["f4b59725-4480-48e8-a91f-3981c8315fdb"])
    total_spend_inr: Decimal = Field(examples=["248563.75"])
    total_spend_usd: Decimal = Field(examples=["1835.20"])
    top_merchants: list[dict[str, Any]] = Field(
        examples=[[{"merchant": "Flipkart", "total": "42123.50"}]]
    )
    category_breakdown: dict[str, Any] = Field(
        examples=[{"Food": "12345.50", "Travel": "25000.00"}]
    )
    anomaly_count: int = Field(examples=[4])
    narrative: str | None = Field(
        default=None,
        examples=[
            "Spending is concentrated across shopping and food, with a few high-value transactions requiring review."
        ],
    )
    risk_level: str | None = Field(default=None, examples=["medium"])
    created_at: datetime
