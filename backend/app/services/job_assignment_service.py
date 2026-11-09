
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import JobCard, JobAssignment, Technician, ServiceBay


ACTIVE_ASSIGNMENT_STATUSES = [
    "ASSIGNED",
    "IN_PROGRESS",
    "ON_HOLD"
]

VALID_ASSIGNMENT_STATUSES = [
    "ASSIGNED",
    "IN_PROGRESS",
    "ON_HOLD",
    "COMPLETED",
    "CANCELLED"
]

VALID_STATUS_TRANSITIONS = {
    "ASSIGNED": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["ON_HOLD", "COMPLETED", "CANCELLED"],
    "ON_HOLD": ["IN_PROGRESS", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": []
}


def create_job_assignment(
    db: Session,
    job_card_id: int,
    technician_id: int,
    service_bay_id: int
):
    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise ValueError("Job card not found.")

    if job_card.status in ["COMPLETED", "CANCELLED"]:
        raise ValueError(
            "Cannot assign a completed or cancelled job card."
        )

    technician = db.query(Technician).filter(
        Technician.id == technician_id
    ).first()

    if not technician:
        raise ValueError("Technician not found.")

    if not technician.is_available:
        raise ValueError("Technician is not available.")

    service_bay = db.query(ServiceBay).filter(
        ServiceBay.id == service_bay_id
    ).first()

    if not service_bay:
        raise ValueError("Service bay not found.")

    if not service_bay.is_active:
        raise ValueError("Service bay is not active.")

    technician_conflict = db.query(JobAssignment).filter(
        JobAssignment.technician_id == technician_id,
        JobAssignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
        JobAssignment.job_card_id != job_card_id
    ).first()

    if technician_conflict:
        raise ValueError(
            "Technician already has an active job assignment."
        )

    bay_conflict = db.query(JobAssignment).filter(
        JobAssignment.service_bay_id == service_bay_id,
        JobAssignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
        JobAssignment.job_card_id != job_card_id
    ).first()

    if bay_conflict:
        raise ValueError(
            "Service bay already has an active job assignment."
        )

    existing_assignments = db.query(JobAssignment).filter(
        JobAssignment.job_card_id == job_card_id,
        JobAssignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES)
    ).all()

    for assignment in existing_assignments:
        assignment.status = "CANCELLED"

    new_assignment = JobAssignment(
        job_card_id=job_card_id,
        technician_id=technician_id,
        service_bay_id=service_bay_id,
        status="ASSIGNED"
    )

    db.add(new_assignment)

    try:
        db.commit()
        db.refresh(new_assignment)
        return new_assignment
    except Exception:
        db.rollback()
        raise


def get_job_assignment(
    db: Session,
    assignment_id: int
):
    assignment = db.query(JobAssignment).filter(
        JobAssignment.id == assignment_id
    ).first()

    if not assignment:
        raise ValueError("Job assignment not found.")

    return assignment


def get_job_assignments(db: Session):
    return db.query(JobAssignment).order_by(
        JobAssignment.assigned_at.desc()
    ).all()


def update_job_assignment_status(
    db: Session,
    assignment_id: int,
    new_status: str
):
    assignment = get_job_assignment(db, assignment_id)

    new_status = new_status.upper()

    if new_status not in VALID_ASSIGNMENT_STATUSES:
        raise ValueError("Invalid job assignment status.")

    allowed_transitions = VALID_STATUS_TRANSITIONS[
        assignment.status
    ]

    if new_status not in allowed_transitions:
        raise ValueError(
            f"Cannot change assignment status from "
            f"{assignment.status} to {new_status}."
        )

    now = datetime.now(timezone.utc)

    if new_status == "IN_PROGRESS":
        assignment.started_at = now

    if new_status == "COMPLETED":
        assignment.completed_at = now

    assignment.status = new_status

    try:
        db.commit()
        db.refresh(assignment)
        return assignment
    except Exception:
        db.rollback()
        raise
