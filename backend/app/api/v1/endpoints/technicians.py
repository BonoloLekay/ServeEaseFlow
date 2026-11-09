from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User

from app.schemas.technician import (
    TechnicianCreate,
    TechnicianUpdate,
    TechnicianResponse
)

from app.services.technician_service import (
    create_technician,
    get_technician,
    get_technicians,
    update_technician
)


router = APIRouter(
    prefix="/technicians",
    tags=["Technicians"]
)


@router.post(
    "/",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED
)
def create_technician_endpoint(
    technician_data: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return create_technician(
            db=db,
            technician_data=technician_data
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[TechnicianResponse]
)
def list_technicians_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    return get_technicians(db)


@router.get(
    "/{technician_id}",
    response_model=TechnicianResponse
)
def get_technician_endpoint(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    try:
        return get_technician(
            db=db,
            technician_id=technician_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.put(
    "/{technician_id}",
    response_model=TechnicianResponse
)
def update_technician_endpoint(
    technician_id: int,
    technician_data: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    )
):
    try:
        return update_technician(
            db=db,
            technician_id=technician_id,
            technician_data=technician_data
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )