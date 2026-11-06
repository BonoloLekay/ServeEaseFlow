from datetime import datetime, timezone

from sqlalchemy import Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobCardPart(Base):
    __tablename__ = "job_card_parts"

    __table_args__ = (
        UniqueConstraint(
            "job_card_id",
            "part_id",
            name="uq_job_card_part"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    job_card_id: Mapped[int] = mapped_column(
        ForeignKey("job_cards.id"),
        nullable=False
    )

    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id"),
        nullable=False
    )

    quantity_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[float] = mapped_column(
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
        back_populates="parts_used"
    )

    part = relationship(
        "Part",
        back_populates="job_card_parts"
    )