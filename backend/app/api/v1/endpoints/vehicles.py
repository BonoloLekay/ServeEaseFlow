from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.core.dependencies import require_roles
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse
)
from app.services.vehicle_service import (
    get_customer_vehicles,
    get_customer_vehicle,
    create_customer_vehicle,
    update_customer_vehicle,
    delete_customer_vehicle
)


router = APIRouter(
    prefix="/vehicles",
    tags=["Customer Vehicles"]
)


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_vehicle(
    vehicle_data: VehicleCreate,
    current_user: User = Depends(require_roles("CUSTOMER")),
    db: Session = Depends(get_db)
):
    try:
        return create_customer_vehicle(
            db=db,
            customer_id=current_user.customer.id,
            registration_number=vehicle_data.registration_number,
            vin=vehicle_data.vin,
            make=vehicle_data.make,
            model=vehicle_data.model,
            year=vehicle_data.year,
            colour=vehicle_data.colour
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[VehicleResponse]
)
def list_vehicles(
    current_user: User = Depends(require_roles("CUSTOMER")),
    db: Session = Depends(get_db)
):
    return get_customer_vehicles(
        db,
        current_user.customer.id
    )


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse
)
def get_vehicle(
    vehicle_id: int,
    current_user: User = Depends(require_roles("CUSTOMER")),
    db: Session = Depends(get_db)
):
    vehicle = get_customer_vehicle(
        db,
        current_user.customer.id,
        vehicle_id
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found."
        )

    return vehicle


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse
)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    current_user: User = Depends(require_roles("CUSTOMER")),
    db: Session = Depends(get_db)
):
    vehicle = get_customer_vehicle(
        db,
        current_user.customer.id,
        vehicle_id
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found."
        )

    try:
        return update_customer_vehicle(
            db,
            vehicle,
            **vehicle_data.model_dump(exclude_unset=True)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_vehicle(
    vehicle_id: int,
    current_user: User = Depends(require_roles("CUSTOMER")),
    db: Session = Depends(get_db)
):
    vehicle = get_customer_vehicle(
        db,
        current_user.customer.id,
        vehicle_id
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found."
        )

    try:
        delete_customer_vehicle(db, vehicle)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle cannot be deleted because it may have related records."
        )