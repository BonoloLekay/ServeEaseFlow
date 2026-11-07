
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Appointment, Vehicle, ServiceCategory


def generate_booking_reference(db: Session):
    while True:
        reference = f"SE-{secrets.token_hex(5).upper()}"

        existing = db.query(Appointment).filter(
            Appointment.booking_reference == reference
        ).first()

        if not existing:
            return reference


def get_customer_appointments(
    db: Session,
    customer_id: int
):
    return db.query(Appointment).join(
        Vehicle,
        Appointment.vehicle_id == Vehicle.id
    ).filter(
        Vehicle.customer_id == customer_id
    ).order_by(
        Appointment.scheduled_at.desc()
    ).all()


def get_customer_appointment(
    db: Session,
    customer_id: int,
    appointment_id: int
):
    return db.query(Appointment).join(
        Vehicle,
        Appointment.vehicle_id == Vehicle.id
    ).filter(
        Appointment.id == appointment_id,
        Vehicle.customer_id == customer_id
    ).first()


def create_customer_appointment(
    db: Session,
    customer_id: int,
    vehicle_id: int,
    service_category_id: int,
    scheduled_at: datetime,
    customer_notes: str | None = None
):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.customer_id == customer_id
    ).first()

    if not vehicle:
        raise ValueError(
            "Vehicle not found or does not belong to this customer."
        )

    service_category = db.query(ServiceCategory).filter(
        ServiceCategory.id == service_category_id,
        ServiceCategory.is_active.is_(True)
    ).first()

    if not service_category:
        raise ValueError(
            "Service category not found or is inactive."
        )

    if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
        raise ValueError(
            "Appointment date and time must include a timezone."
        )

    if scheduled_at <= datetime.now(timezone.utc):
        raise ValueError(
            "Appointment must be scheduled for a future date and time."
        )

    appointment = Appointment(
        booking_reference=generate_booking_reference(db),
        vehicle_id=vehicle_id,
        service_category_id=service_category_id,
        scheduled_at=scheduled_at,
        status="PENDING",
        customer_notes=customer_notes
    )

    try:
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return appointment

    except Exception:
        db.rollback()
        raise


def update_customer_appointment(
    db: Session,
    appointment: Appointment,
    vehicle_id: int | None = None,
    service_category_id: int | None = None,
    scheduled_at: datetime | None = None,
    customer_notes: str | None = None
):
    if appointment.job_card is not None:
        raise ValueError(
            "Appointments with an existing job card cannot be updated."
        )

    if appointment.status != "PENDING":
        raise ValueError(
            "Only pending appointments can be updated."
        )

    if vehicle_id is not None:
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.customer_id == appointment.vehicle.customer_id
        ).first()

        if not vehicle:
            raise ValueError(
                "Vehicle not found or does not belong to this customer."
            )

        appointment.vehicle_id = vehicle_id

    if service_category_id is not None:
        service_category = db.query(ServiceCategory).filter(
            ServiceCategory.id == service_category_id,
            ServiceCategory.is_active.is_(True)
        ).first()

        if not service_category:
            raise ValueError(
                "Service category not found or is inactive."
            )

        appointment.service_category_id = service_category_id

    if scheduled_at is not None:
        if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
            raise ValueError(
                "Appointment date and time must include a timezone."
            )

        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError(
                "Appointment must be scheduled for a future date and time."
            )

        appointment.scheduled_at = scheduled_at

    if customer_notes is not None:
        appointment.customer_notes = customer_notes

    try:
        db.commit()
        db.refresh(appointment)

        return appointment

    except Exception:
        db.rollback()
        raise


def cancel_customer_appointment(
    db: Session,
    appointment: Appointment
):
    if appointment.job_card is not None:
        raise ValueError(
            "Appointments with an existing job card cannot be cancelled."
        )

    if appointment.status != "PENDING":
        raise ValueError(
            "Only pending appointments can be cancelled."
        )

    try:
        appointment.status = "CANCELLED"

        db.commit()
        db.refresh(appointment)

        return appointment

    except Exception:
        db.rollback()
        raise
