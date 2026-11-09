from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User
from app.schemas.invoice import InvoiceResponse

from app.services.invoice_service import (
    generate_invoice,
    get_invoice,
    get_job_card_invoice,
    get_all_invoices
)


router = APIRouter(
    prefix="/invoices",
    tags=["Invoice Management"]
)

@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED
)
def generate_invoice_endpoint(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return generate_invoice(db, job_card_id)

    except ValueError as error:
        message = str(error)

        if message == "Job card not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )


@router.get(
    "/",
    response_model=list[InvoiceResponse]
)
def list_invoices_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    return get_all_invoices(db)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse
)
def get_invoice_endpoint(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    invoice = get_invoice(db, invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found."
        )

    return invoice


@router.get(
    "/job-cards/{job_card_id}",
    response_model=InvoiceResponse
)
def get_job_card_invoice_endpoint(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION", "OWNER")
    )
):
    invoice = get_job_card_invoice(db, job_card_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found for this job card."
        )

    return invoice