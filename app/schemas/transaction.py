from __future__ import annotations

from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(examples=["0b769809-f177-42a1-b54a-93f36450d8c8"])
    job_id: UUID = Field(examples=["f4b59725-4480-48e8-a91f-3981c8315fdb"])
    txn_id: str | None = Field(default=None, examples=["TXN1065"])
    date: DateType | None = Field(default=None, examples=["2024-09-04"])
    merchant: str = Field(examples=["Swiggy"])
    amount: Decimal = Field(examples=["11325.79"])
    currency: str = Field(examples=["INR"])
    status: str = Field(examples=["SUCCESS"])
    original_category: str | None = Field(default=None, examples=[None])
    final_category: str = Field(examples=["Food"])
    account_id: str = Field(examples=["ACC004"])
    notes: str | None = Field(default=None, examples=["Refund expected"])
    is_anomaly: bool = Field(examples=[False])
    anomaly_reason: str | None = Field(default=None, examples=[None])
    llm_raw_response: str | None = Field(default=None)
    llm_failed: bool = Field(examples=[False])
    created_at: datetime
