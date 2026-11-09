from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User
from app.schemas.job_card import (
    JobCardCreate,
    JobCardUpdate,
    JobCardStatusUpdate,
    JobCardResponse
)
from app.services.job_card_service import (
    get_job_cards,
    get_job_card,
    create_job_card,
    update_job_card,
    update_job_card_status
)


router = APIRouter(
    prefix="/job-cards",
    tags=["Job Cards"]
)


@router.post(
    "/",
    response_model=JobCardResponse,
    status_code=status.HTTP_201_CREATED
)
def create_job_card_endpoint(
    job_card_data: JobCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return create_job_card(
            db=db,
            vehicle_id=job_card_data.vehicle_id,
            reported_issue=job_card_data.reported_issue,
            appointment_id=job_card_data.appointment_id,
            odometer_reading=job_card_data.odometer_reading
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[JobCardResponse]
)
def list_job_cards_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "ADMIN",
            "RECEPTION",
            "TECHNICIAN",
            "OWNER"
        )
    )
):
    return get_job_cards(db)


@router.get(
    "/{job_card_id}",
    response_model=JobCardResponse
)
def get_job_card_endpoint(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "ADMIN",
            "RECEPTION",
            "TECHNICIAN",
            "OWNER"
        )
    )
):
    job_card = get_job_card(db, job_card_id)

    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job card not found."
        )

    return job_card


@router.put(
    "/{job_card_id}",
    response_model=JobCardResponse
)
def update_job_card_endpoint(
    job_card_id: int,
    job_card_data: JobCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    )
):
    job_card = get_job_card(db, job_card_id)

    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job card not found."
        )

    if not job_card_data.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided."
        )

    try:
        return update_job_card(
            db=db,
            job_card=job_card,
            **job_card_data.model_dump(exclude_unset=True)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.patch(
    "/{job_card_id}/status",
    response_model=JobCardResponse
)
def update_job_card_status_endpoint(
    job_card_id: int,
    status_data: JobCardStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    )
):
    job_card = get_job_card(db, job_card_id)

    if not job_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job card not found."
        )

    try:
        return update_job_card_status(
            db=db,
            job_card=job_card,
            new_status=status_data.status
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )