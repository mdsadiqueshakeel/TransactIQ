import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job_summary import JobSummary
    from app.models.transaction import Transaction


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    row_count_raw: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    row_count_clean: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_failed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    summary: Mapped["JobSummary | None"] = relationship(
        back_populates="job", cascade="all, delete-orphan", uselist=False
    )
