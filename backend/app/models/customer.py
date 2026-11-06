from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    customer_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    province: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="customer"
    )

    vehicles = relationship(
        "Vehicle",
        back_populates="customer",
        cascade="all, delete-orphan"
    )