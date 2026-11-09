import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import JobCard, Vehicle, Appointment


def generate_job_card_number(db: Session):
    while True:
        number = f"JC-{secrets.token_hex(5).upper()}"

        existing = db.query(JobCard).filter(
            JobCard.job_card_number == number
        ).first()

        if not existing:
            return number


def get_job_cards(db: Session):
    return db.query(JobCard).order_by(
        JobCard.created_at.desc()
    ).all()


def get_job_card(db: Session, job_card_id: int):
    return db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()


def create_job_card(
    db: Session,
    vehicle_id: int,
    reported_issue: str,
    appointment_id: int | None = None,
    odometer_reading: int | None = None
):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if not vehicle:
        raise ValueError("Vehicle not found.")

    if appointment_id is not None:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise ValueError("Appointment not found.")

        if appointment.vehicle_id != vehicle_id:
            raise ValueError(
                "The appointment does not belong to this vehicle."
            )

        existing_job_card = db.query(JobCard).filter(
            JobCard.appointment_id == appointment_id
        ).first()

        if existing_job_card:
            raise ValueError(
                "A job card already exists for this appointment."
            )

    job_card = JobCard(
        job_card_number=generate_job_card_number(db),
        appointment_id=appointment_id,
        vehicle_id=vehicle_id,
        reported_issue=reported_issue,
        odometer_reading=odometer_reading,
        status="OPEN"
    )

    try:
        db.add(job_card)
        db.commit()
        db.refresh(job_card)

        return job_card

    except Exception:
        db.rollback()
        raise


def update_job_card(
    db: Session,
    job_card: JobCard,
    reported_issue: str | None = None,
    diagnosis: str | None = None,
    work_performed: str | None = None,
    odometer_reading: int | None = None
):
    if job_card.status in ("COMPLETED", "CANCELLED"):
        raise ValueError(
            "Completed or cancelled job cards cannot be updated."
        )

    if reported_issue is not None:
        job_card.reported_issue = reported_issue

    if diagnosis is not None:
        job_card.diagnosis = diagnosis

    if work_performed is not None:
        job_card.work_performed = work_performed

    if odometer_reading is not None:
        job_card.odometer_reading = odometer_reading

    try:
        db.commit()
        db.refresh(job_card)

        return job_card

    except Exception:
        db.rollback()
        raise


def update_job_card_status(
    db: Session,
    job_card: JobCard,
    new_status: str
):
    allowed_transitions = {
        "OPEN": ["IN_PROGRESS", "CANCELLED"],
        "IN_PROGRESS": ["ON_HOLD", "COMPLETED", "CANCELLED"],
        "ON_HOLD": ["IN_PROGRESS", "CANCELLED"],
        "COMPLETED": [],
        "CANCELLED": []
    }

    new_status = new_status.upper()

    if new_status not in allowed_transitions:
        raise ValueError("Invalid job card status.")

    current_status = job_card.status

    if new_status not in allowed_transitions.get(
        current_status,
        []
    ):
        raise ValueError(
            f"Cannot change job card status from "
            f"{current_status} to {new_status}."
        )

    try:
        job_card.status = new_status

        if new_status == "COMPLETED":
            job_card.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job_card)

        return job_card

    except Exception:
        db.rollback()
        raise