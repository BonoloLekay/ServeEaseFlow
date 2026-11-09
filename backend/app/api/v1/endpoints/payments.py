
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.models.invoice import Invoice
from app.core.dependencies import get_current_user
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentCheckoutResponse
)
from app.services.payment_service import (
    create_pending_payment,
    generate_payfast_checkout,
    get_payment,
    get_invoice_payments,
    get_all_payments,
    verify_invoice_ownership
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post(
    "/",
    response_model=PaymentCheckoutResponse,
    status_code=status.HTTP_201_CREATED
)
def create_payment_endpoint(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = current_user.role.name

    if role not in {"CUSTOMER", "ADMIN", "RECEPTION"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to initiate payments."
        )

    if role == "CUSTOMER":
        try:
            verify_invoice_ownership(
                db,
                payment_data.invoice_id,
                current_user.id
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error)
            )

    try:
        payment = create_pending_payment(
            db,
            payment_data.invoice_id
        )

        return generate_payfast_checkout(
            db,
            payment
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[PaymentResponse]
)
def list_payments_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.name not in {
        "ADMIN", "RECEPTION", "OWNER"
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view all payments."
        )

    return get_all_payments(db)


@router.get(
    "/invoice/{invoice_id}",
    response_model=list[PaymentResponse]
)
def get_invoice_payments_endpoint(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = current_user.role.name

    # Confirm that the invoice exists.
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .first()
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found."
        )

    # Customers can only view payments for their own invoices.
    if role == "CUSTOMER":
        try:
            verify_invoice_ownership(
                db,
                invoice_id,
                current_user.id
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error)
            )

    elif role not in {"ADMIN", "RECEPTION", "OWNER"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view these payments."
        )

    return get_invoice_payments(db, invoice_id)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse
)
def get_payment_endpoint(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = get_payment(db, payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found."
        )

    role = current_user.role.name

    # Customers can only view their own payments.
    if role == "CUSTOMER":
        try:
            verify_invoice_ownership(
                db,
                payment.invoice_id,
                current_user.id
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found."
            )

    elif role not in {"ADMIN", "RECEPTION", "OWNER"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this payment."
        )

    return payment
