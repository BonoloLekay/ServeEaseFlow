from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User

from app.schemas.service_bay import (
    ServiceBayCreate,
    ServiceBayUpdate,
    ServiceBayResponse
)

from app.services.service_bay_service import (
    create_service_bay,
    get_service_bay,
    get_service_bays,
    update_service_bay
)


router = APIRouter(
    prefix="/service-bays",
    tags=["Service Bays"]
)


@router.post(
    "/",
    response_model=ServiceBayResponse,
    status_code=status.HTTP_201_CREATED
)
def create_service_bay_endpoint(
    bay_data: ServiceBayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    )
):
    try:
        return create_service_bay(
            db=db,
            bay_data=bay_data
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[ServiceBayResponse]
)
def list_service_bays_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    return get_service_bays(db)


@router.get(
    "/{bay_id}",
    response_model=ServiceBayResponse
)
def get_service_bay_endpoint(
    bay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    try:
        return get_service_bay(
            db=db,
            bay_id=bay_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.put(
    "/{bay_id}",
    response_model=ServiceBayResponse
)
def update_service_bay_endpoint(
    bay_id: int,
    bay_data: ServiceBayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    )
):
    try:
        return update_service_bay(
            db=db,
            bay_id=bay_id,
            bay_data=bay_data
        )

    except ValueError as error:
        status_code_value = (
            status.HTTP_404_NOT_FOUND
            if str(error) == "Service bay not found."
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=status_code_value,
            detail=str(error)
        )