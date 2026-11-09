
from sqlalchemy.orm import Session

from app.models import (
    Part,
    JobCard,
    JobCardPart,
    InventoryTransaction
)


def get_part_transactions(db: Session, part_id: int):
    return db.query(InventoryTransaction).filter(
        InventoryTransaction.part_id == part_id
    ).order_by(
        InventoryTransaction.created_at.desc()
    ).all()


def receive_stock(
    db: Session,
    part_id: int,
    quantity: int,
    reference: str | None = None,
    notes: str | None = None
):
    part = db.query(Part).filter(
        Part.id == part_id
    ).with_for_update().first()

    if not part:
        raise ValueError("Part not found.")

    if not part.is_active:
        raise ValueError("Inactive parts cannot receive stock.")

    part.quantity_in_stock += quantity

    transaction = InventoryTransaction(
        part_id=part.id,
        transaction_type="STOCK_IN",
        quantity=quantity,
        reference=reference,
        notes=notes
    )

    try:
        db.add(transaction)
        db.commit()
        db.refresh(part)
        return part

    except Exception:
        db.rollback()
        raise


def issue_stock(
    db: Session,
    part_id: int,
    quantity: int,
    reference: str | None = None,
    notes: str | None = None
):
    part = db.query(Part).filter(
        Part.id == part_id
    ).with_for_update().first()

    if not part:
        raise ValueError("Part not found.")

    if not part.is_active:
        raise ValueError("Inactive parts cannot be issued.")

    if part.quantity_in_stock < quantity:
        raise ValueError("Insufficient stock available.")

    part.quantity_in_stock -= quantity

    transaction = InventoryTransaction(
        part_id=part.id,
        transaction_type="STOCK_OUT",
        quantity=quantity,
        reference=reference,
        notes=notes
    )

    try:
        db.add(transaction)
        db.commit()
        db.refresh(part)
        return part

    except Exception:
        db.rollback()
        raise


def add_part_to_job_card(
    db: Session,
    job_card_id: int,
    part_id: int,
    quantity_used: int
):
    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise ValueError("Job card not found.")

    if job_card.status in ("COMPLETED", "CANCELLED"):
        raise ValueError(
            "Parts cannot be added to completed or cancelled job cards."
        )

    part = db.query(Part).filter(
        Part.id == part_id
    ).with_for_update().first()

    if not part:
        raise ValueError("Part not found.")

    if not part.is_active:
        raise ValueError("Inactive parts cannot be used.")

    if part.quantity_in_stock < quantity_used:
        raise ValueError("Insufficient stock available.")

    try:
        job_card_part = db.query(JobCardPart).filter(
            JobCardPart.job_card_id == job_card_id,
            JobCardPart.part_id == part_id
        ).first()

        if job_card_part:
            job_card_part.quantity_used += quantity_used

        else:
            job_card_part = JobCardPart(
                job_card_id=job_card_id,
                part_id=part_id,
                quantity_used=quantity_used,
                unit_price=part.selling_price
            )
            db.add(job_card_part)

        part.quantity_in_stock -= quantity_used

        transaction = InventoryTransaction(
            part_id=part_id,
            transaction_type="JOB_CARD_USAGE",
            quantity=quantity_used,
            reference=f"Job Card ID: {job_card_id}",
            notes="Part issued for job card."
        )

        db.add(transaction)
        db.commit()
        db.refresh(job_card_part)

        return job_card_part

    except Exception:
        db.rollback()
        raise
