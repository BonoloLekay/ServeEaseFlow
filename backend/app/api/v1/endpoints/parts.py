
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User
from app.schemas.part import (
    PartCreate,
    PartUpdate,
    PartResponse,
    StockMovementCreate,
    InventoryTransactionResponse,
    JobCardPartCreate,
    JobCardPartResponse
)
from app.services.part_service import (
    get_parts,
    get_part,
    create_part,
    update_part,
    get_low_stock_parts
)
from app.services.inventory_service import (
    get_part_transactions,
    receive_stock,
    issue_stock,
    add_part_to_job_card
)


router = APIRouter(
    prefix="/parts",
    tags=["Parts & Inventory"]
)


@router.get("/low-stock", response_model=list[PartResponse])
def low_stock_parts_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    return get_low_stock_parts(db)


@router.post(
    "/",
    response_model=PartResponse,
    status_code=status.HTTP_201_CREATED
)
def create_part_endpoint(
    part_data: PartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    try:
        return create_part(
            db,
            part_data.model_dump()
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get("/", response_model=list[PartResponse])
def list_parts_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "TECHNICIAN", "OWNER")
    )
):
    return get_parts(db)


@router.get("/{part_id}", response_model=PartResponse)
def get_part_endpoint(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "TECHNICIAN", "OWNER")
    )
):
    part = get_part(db, part_id)

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found."
        )

    return part


@router.put("/{part_id}", response_model=PartResponse)
def update_part_endpoint(
    part_id: int,
    part_data: PartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    part = get_part(db, part_id)

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found."
        )

    if not part_data.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided."
        )

    return update_part(
        db,
        part,
        part_data.model_dump(exclude_unset=True)
    )


@router.post("/{part_id}/stock-in", response_model=PartResponse)
def receive_stock_endpoint(
    part_id: int,
    movement: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return receive_stock(
            db,
            part_id,
            movement.quantity,
            movement.reference,
            movement.notes
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.post("/{part_id}/stock-out", response_model=PartResponse)
def issue_stock_endpoint(
    part_id: int,
    movement: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return issue_stock(
            db,
            part_id,
            movement.quantity,
            movement.reference,
            movement.notes
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/{part_id}/transactions",
    response_model=list[InventoryTransactionResponse]
)
def part_transactions_endpoint(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    if not get_part(db, part_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Part not found."
        )

    return get_part_transactions(db, part_id)


@router.post(
    "/job-cards/{job_card_id}/usage",
    response_model=JobCardPartResponse,
    status_code=status.HTTP_201_CREATED
)
def add_part_to_job_card_endpoint(
    job_card_id: int,
    part_data: JobCardPartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "TECHNICIAN")
    )
):
    try:
        return add_part_to_job_card(
            db,
            job_card_id,
            part_data.part_id,
            part_data.quantity_used
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
