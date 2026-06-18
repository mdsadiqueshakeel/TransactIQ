import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job import Job


class JobSummary(Base):
    __tablename__ = "job_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    total_spend_inr: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    total_spend_usd: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    top_merchants: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    category_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    anomaly_count: Mapped[int] = mapped_column(nullable=False, default=0)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    job: Mapped["Job"] = relationship(back_populates="summary")
