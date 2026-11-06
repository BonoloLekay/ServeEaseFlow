from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    part_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    quantity_in_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    reorder_level: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False
    )

    unit_cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    selling_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
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

    job_card_parts = relationship(
        "JobCardPart",
        back_populates="part"
    )

    inventory_transactions = relationship(
        "InventoryTransaction",
        back_populates="part"
    )