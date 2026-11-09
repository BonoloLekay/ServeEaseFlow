from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User
from app.schemas.labour_entry import (
    LabourEntryCreate,
    LabourEntryUpdate,
    LabourEntryResponse
)
from app.services.labour_service import (
    create_labour_entry,
    get_labour_entry,
    get_job_card_labour,
    update_labour_entry,
    calculate_labour_total
)


router = APIRouter(
    prefix="/labour",
    tags=["Labour Management"]
)


@router.post(
    "/",
    response_model=LabourEntryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_labour_entry_endpoint(
    labour_data: LabourEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return create_labour_entry(
            db,
            labour_data.job_card_id,
            labour_data.technician_id,
            labour_data.description,
            labour_data.hours_worked,
            labour_data.hourly_rate
        )
    except ValueError as error:
        error_message = str(error)

        if error_message in [
            "Job card not found.",
            "Technician not found."
        ]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_message
    )


@router.get(
    "/job-cards/{job_card_id}",
    response_model=list[LabourEntryResponse]
)
def list_job_card_labour_endpoint(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "TECHNICIAN", "OWNER")
    )
):
    try:
        return get_job_card_labour(db, job_card_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get(
    "/job-cards/{job_card_id}/total"
)
def job_card_labour_total_endpoint(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    try:
        entries = get_job_card_labour(db, job_card_id)
        total = calculate_labour_total(entries)

        return {
            "job_card_id": job_card_id,
            "labour_total": total
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.put(
    "/{entry_id}",
    response_model=LabourEntryResponse
)
def update_labour_entry_endpoint(
    entry_id: int,
    labour_data: LabourEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    entry = get_labour_entry(db, entry_id)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Labour entry not found."
        )

    if not labour_data.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided."
        )

    if any(
        value is None
        for value in labour_data.model_dump(exclude_unset=True).values()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Labour entry fields cannot be null."
        )

    try:
        return update_labour_entry(
            db,
            entry,
            labour_data.model_dump(exclude_unset=True)
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
