from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobAssignment(Base):
    __tablename__ = "job_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

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

    service_bay_id: Mapped[int] = mapped_column(
        ForeignKey("service_bays.id"),
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ASSIGNED",
        nullable=False
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    job_card = relationship(
        "JobCard",
        back_populates="assignments"
    )

    technician = relationship(
        "Technician",
        back_populates="assignments"
    )

    service_bay = relationship(
        "ServiceBay",
        back_populates="assignments"
    )