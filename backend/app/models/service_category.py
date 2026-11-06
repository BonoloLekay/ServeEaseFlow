from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    base_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    estimated_duration_hours: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    appointments = relationship(
        "Appointment",
        back_populates="service_category"
    )