
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentCheckoutResponse
)
from app.services.payment_service import (
    create_pending_payment,
    generate_payfast_checkout,
    get_payment,
    get_payment_by_reference,
    get_invoice_payments,
    get_all_payments,
    verify_invoice_ownership,
    verify_payfast_itn_signature,
    verify_payfast_source_ip,
    validate_payfast_itn
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


@router.post("/payfast/notify")
async def payfast_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    raw_body = await request.body()

    try:
        parsed_fields = parse_qsl(
            raw_body.decode("utf-8"),
            keep_blank_values=True
        )

        data = dict(parsed_fields)

        if len(data) != len(parsed_fields):
            raise ValueError("Duplicate notification fields")

    except (UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification data"
        )

    if not verify_payfast_itn_signature(data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PayFast signature"
        )

    source_ip = request.client.host if request.client else ""

    if not verify_payfast_source_ip(source_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Untrusted PayFast notification source"
        )

    if data.get("merchant_id") != settings.PAYFAST_MERCHANT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PayFast merchant ID mismatch"
        )

    payment_reference = data.get("m_payment_id")

    if not payment_reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment reference"
        )

    payment = get_payment_by_reference(
        db,
        payment_reference
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    try:
        amount_gross = Decimal(data.get("amount_gross", ""))
    except InvalidOperation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment amount"
        )

    if not amount_gross.is_finite():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment amount"
        )

    if abs(amount_gross - payment.amount) > Decimal("0.01"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount mismatch"
        )

    if not validate_payfast_itn(data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PayFast server validation failed"
        )

    payment_status = data.get("payment_status")
    transaction_id = data.get("pf_payment_id")

    if payment_status != "COMPLETE":
        return {"message": "Payment is not complete"}

    if not transaction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing PayFast transaction ID"
        )

    if payment.status == "COMPLETED":
        if payment.payfast_transaction_id == transaction_id:
            return {"message": "Payment already processed"}

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment has already been completed with another transaction"
        )

    if payment.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment cannot be completed from its current status"
        )

    existing_transaction = (
        db.query(Payment)
        .filter(
            Payment.payfast_transaction_id == transaction_id
        )
        .first()
    )

    if existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PayFast transaction has already been used"
        )

    invoice = payment.invoice

    if invoice.status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice has already been paid"
        )

    payment.status = "COMPLETED"
    payment.payfast_transaction_id = transaction_id
    payment.paid_at = datetime.now(timezone.utc)

    invoice.status = "PAID"

    db.commit()

    return {"message": "Payment successfully completed"}

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
