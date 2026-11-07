from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.core.dependencies import require_roles
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse
)
from app.services.appointment_service import (
    get_customer_appointments,
    get_customer_appointment,
    create_customer_appointment,
    update_customer_appointment,
    cancel_customer_appointment
)


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def get_customer_id(current_user: User) -> int:
    if not current_user.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer profile not found."
        )

    return current_user.customer.id


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("CUSTOMER"))
):
    customer_id = get_customer_id(current_user)

    try:
        return create_customer_appointment(
            db=db,
            customer_id=customer_id,
            vehicle_id=appointment_data.vehicle_id,
            service_category_id=appointment_data.service_category_id,
            scheduled_at=appointment_data.scheduled_at,
            customer_notes=appointment_data.customer_notes
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[AppointmentResponse]
)
def list_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("CUSTOMER"))
):
    customer_id = get_customer_id(current_user)

    return get_customer_appointments(
        db=db,
        customer_id=customer_id
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("CUSTOMER"))
):
    customer_id = get_customer_id(current_user)

    appointment = get_customer_appointment(
        db=db,
        customer_id=customer_id,
        appointment_id=appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found."
        )

    return appointment


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("CUSTOMER"))
):
    customer_id = get_customer_id(current_user)

    appointment = get_customer_appointment(
        db=db,
        customer_id=customer_id,
        appointment_id=appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found."
        )

    if not appointment_data.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided."
        )

    try:
        return update_customer_appointment(
            db=db,
            appointment=appointment,
            vehicle_id=appointment_data.vehicle_id,
            service_category_id=appointment_data.service_category_id,
            scheduled_at=appointment_data.scheduled_at,
            customer_notes=appointment_data.customer_notes
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_200_OK
)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("CUSTOMER"))
):
    customer_id = get_customer_id(current_user)

    appointment = get_customer_appointment(
        db=db,
        customer_id=customer_id,
        appointment_id=appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found."
        )

    try:
        cancelled_appointment = cancel_customer_appointment(
            db=db,
            appointment=appointment
        )

        return {
            "message": "Appointment cancelled successfully.",
            "booking_reference": cancelled_appointment.booking_reference,
            "status": cancelled_appointment.status
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )