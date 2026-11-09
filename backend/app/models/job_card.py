from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobCard(Base):
    __tablename__ = "job_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    job_card_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id"),
        unique=True,
        nullable=True
    )

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"),
        nullable=False,
        index=True
    )

    reported_issue: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    work_performed: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    odometer_reading: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN",
        nullable=False
    )

    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    appointment = relationship(
        "Appointment",
        back_populates="job_card"
    )

    vehicle = relationship("Vehicle")

    assignments = relationship(
        "JobAssignment",
        back_populates="job_card"
    )

    parts_used = relationship(
        "JobCardPart",
        back_populates="job_card"
    )

    invoice = relationship(
        "Invoice",
        back_populates="job_card",
        uselist=False
    )

    labour_entries = relationship(
        "LabourEntry",
        back_populates="job_card"
    )