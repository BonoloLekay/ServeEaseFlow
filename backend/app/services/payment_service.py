import hmac
import requests
import socket
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.job_card import JobCard
from app.models.customer import Customer
from app.models.vehicle import Vehicle

import hashlib
from urllib.parse import quote_plus

from app.core.config import settings

def create_pending_payment(
    db: Session,
    invoice_id: int
) -> Payment:

    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .first()
    )

    if not invoice:
        raise ValueError("Invoice not found.")

    if invoice.status == "PAID":
        raise ValueError("This invoice has already been paid.")

    if invoice.total_amount <= 0:
        raise ValueError("Invoice amount must be greater than zero.")

    # Reuse an existing pending payment.
    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.invoice_id == invoice.id,
            Payment.status == "PENDING"
        )
        .first()
    )

    if existing_payment:
        return existing_payment

    payment = Payment(
        invoice_id=invoice.id,
        payment_reference=f"SE-{uuid4().hex[:12].upper()}",
        amount=invoice.total_amount,
        payment_method="PAYFAST",
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_payment(
    db: Session,
    payment_id: int
) -> Payment | None:

    return (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )


def get_payment_by_reference(
    db: Session,
    payment_reference: str
) -> Payment | None:

    return (
        db.query(Payment)
        .filter(
            Payment.payment_reference == payment_reference
        )
        .first()
    )


def get_invoice_payments(
    db: Session,
    invoice_id: int
) -> list[Payment]:

    return (
        db.query(Payment)
        .filter(Payment.invoice_id == invoice_id)
        .order_by(Payment.created_at.desc())
        .all()
    )


def get_all_payments(db: Session) -> list[Payment]:

    return (
        db.query(Payment)
        .order_by(Payment.created_at.desc())
        .all()
    )


def verify_invoice_ownership(
    db: Session,
    invoice_id: int,
    user_id: int
) -> Invoice:

    invoice = (
        db.query(Invoice)
        .join(JobCard, Invoice.job_card_id == JobCard.id)
        .join(Vehicle, JobCard.vehicle_id == Vehicle.id)
        .join(Customer, Vehicle.customer_id == Customer.id)
        .filter(
            Invoice.id == invoice_id,
            Customer.user_id == user_id
        )
        .first()
    )

    if not invoice:
        raise ValueError(
            "Invoice not found or you do not have access to it."
        )

    return invoice


def generate_payfast_signature(
    data: dict[str, str],
    passphrase: str
) -> str:

    parameter_string = "&".join(
        f"{key}={quote_plus(value.strip())}"
        for key, value in data.items()
        if value != ""
    )

    parameter_string += (
        f"&passphrase={quote_plus(passphrase.strip())}"
    )

    return hashlib.md5(
        parameter_string.encode("utf-8")
    ).hexdigest()

def verify_payfast_itn_signature(
    data: dict[str, str]
) -> bool:
    signature = data.get("signature")

    if not signature or not settings.PAYFAST_PASSPHRASE:
        return False

    signature_data = {
        key: value
        for key, value in data.items()
        if key != "signature"
    }

    expected_signature = generate_payfast_signature(
        signature_data,
        settings.PAYFAST_PASSPHRASE
    )

    return hmac.compare_digest(
        signature.lower(),
        expected_signature.lower()
    )


def validate_payfast_itn(data: dict[str, str]) -> bool:
    validation_data = {
        key: value
        for key, value in data.items()
        if key != "signature"
    }

    try:
        response = requests.post(
            "https://sandbox.payfast.co.za/eng/query/validate",
            data=validation_data,
            timeout=15
        )

        response.raise_for_status()

    except requests.RequestException:
        return False

    return response.text.strip() == "VALID"


def verify_payfast_source_ip(source_ip: str) -> bool:
    payfast_hosts = [
        "www.payfast.co.za",
        "sandbox.payfast.co.za",
        "w1w.payfast.co.za",
        "w2w.payfast.co.za",
    ]

    allowed_ips = set()

    for host in payfast_hosts:
        try:
            _, _, addresses = socket.gethostbyname_ex(host)
            allowed_ips.update(addresses)
        except socket.gaierror:
            continue

    return source_ip in allowed_ips

def generate_payfast_checkout(
    db: Session,
    payment: Payment
) -> dict:

    if not all([
        settings.PAYFAST_MERCHANT_ID,
        settings.PAYFAST_MERCHANT_KEY,
        settings.PAYFAST_PASSPHRASE
    ]):
        raise ValueError(
            "PayFast credentials are not fully configured."
        )

    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == payment.invoice_id)
        .first()
    )

    if not invoice:
        raise ValueError("Invoice not found.")

    job_card = invoice.job_card
    vehicle = job_card.vehicle
    customer = vehicle.customer
    user = customer.user

    data = {
        "merchant_id": settings.PAYFAST_MERCHANT_ID,
        "merchant_key": settings.PAYFAST_MERCHANT_KEY,
        "return_url": (
            f"{settings.FRONTEND_URL}/payment/success"
        ),
        "cancel_url": (
            f"{settings.FRONTEND_URL}/payment/cancel"
        ),
        "notify_url": (
            f"{settings.BACKEND_URL}/api/v1/payments/payfast/notify"
        ),
        "name_first": user.first_name,
        "name_last": user.last_name,
        "email_address": user.email,
        "m_payment_id": payment.payment_reference,
        "amount": f"{payment.amount:.2f}",
        "item_name": f"ServeEase Invoice {invoice.invoice_number}",
        "item_description": (
            f"Vehicle service invoice {invoice.invoice_number}"
        )
    }

    signature = generate_payfast_signature(
        data,
        settings.PAYFAST_PASSPHRASE
    )

    data["signature"] = signature

    return {
        "id": payment.id,
        "invoice_id": payment.invoice_id,
        "payment_reference": payment.payment_reference,
        "payfast_transaction_id": payment.payfast_transaction_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "status": payment.status,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
        "checkout_url": (
            "https://sandbox.payfast.co.za/eng/process"
        ),
        "form_fields": data
    }
