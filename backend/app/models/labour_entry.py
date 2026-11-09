from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LabourEntry(Base):
    __tablename__ = "labour_entries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    job_card_id: Mapped[int] = mapped_column(
        ForeignKey("job_cards.id"),
        nullable=False,
        index=True
    )

    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technicians.id"),
        nullable=False,
        index=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    hours_worked: Mapped[float] = mapped_column(
        Numeric(8, 2),
        nullable=False
    )

    hourly_rate: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    job_card = relationship(
        "JobCard",
        back_populates="labour_entries"
    )

    technician = relationship(
        "Technician",
        back_populates="labour_entries"
    )
