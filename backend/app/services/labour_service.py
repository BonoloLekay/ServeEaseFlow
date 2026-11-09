from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import JobCard, Technician, LabourEntry


def create_labour_entry(
    db: Session,
    job_card_id: int,
    technician_id: int,
    description: str,
    hours_worked: Decimal,
    hourly_rate: Decimal
):
    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise ValueError("Job card not found.")

    if job_card.status in ["COMPLETED", "CANCELLED"]:
        raise ValueError(
            "Cannot add labour to a completed or cancelled job card."
        )

    technician = db.query(Technician).filter(
        Technician.id == technician_id
    ).first()

    if not technician:
        raise ValueError("Technician not found.")    

    entry = LabourEntry(
        job_card_id=job_card_id,
        technician_id=technician_id,
        description=description,
        hours_worked=hours_worked,
        hourly_rate=hourly_rate
    )

    db.add(entry)

    try:
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:
        db.rollback()
        raise


def get_labour_entry(db: Session, entry_id: int):
    return db.query(LabourEntry).filter(
        LabourEntry.id == entry_id
    ).first()


def get_job_card_labour(db: Session, job_card_id: int):
    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise ValueError("Job card not found.")

    return db.query(LabourEntry).filter(
        LabourEntry.job_card_id == job_card_id
    ).order_by(LabourEntry.created_at.asc()).all()


def update_labour_entry(
    db: Session,
    entry: LabourEntry,
    updates: dict
):
    job_card = entry.job_card

    if job_card.status in ["COMPLETED", "CANCELLED"]:
        raise ValueError(
            "Cannot update labour on a completed or cancelled job card."
        )

    for field, value in updates.items():
        setattr(entry, field, value)

    try:
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:
        db.rollback()
        raise


def calculate_labour_total(entries) -> Decimal:
    total = Decimal("0.00")

    for entry in entries:
        total += (
            Decimal(str(entry.hours_worked))
            * Decimal(str(entry.hourly_rate))
        )

    return total.quantize(Decimal("0.01"))
