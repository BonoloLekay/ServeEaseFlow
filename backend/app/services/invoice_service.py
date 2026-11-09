from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.job_card import JobCard


VAT_RATE = Decimal("0.15")
ZERO_AMOUNT = Decimal("0.00")

def calculate_job_card_costs(job_card: JobCard) -> dict:
    labour_total = sum(
        (
            Decimal(str(entry.hours_worked))
            * Decimal(str(entry.hourly_rate))
            for entry in job_card.labour_entries
        ),
        ZERO_AMOUNT
    )

    parts_total = sum(
        (
            Decimal(str(part.quantity_used))
            * Decimal(str(part.unit_price))
            for part in job_card.parts_used
        ),
        ZERO_AMOUNT
    )

    subtotal = labour_total + parts_total

    tax_amount = (
        subtotal * VAT_RATE
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    total_amount = subtotal + tax_amount

    return {
        "labour_total": labour_total.quantize(Decimal("0.01")),
        "parts_total": parts_total.quantize(Decimal("0.01")),
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "tax_amount": tax_amount,
        "total_amount": total_amount.quantize(Decimal("0.01"))
    }

def generate_invoice(db: Session, job_card_id: int) -> Invoice:
    job_card = (
        db.query(JobCard)
        .filter(JobCard.id == job_card_id)
        .first()
    )

    if not job_card:
        raise ValueError("Job card not found.")

    if job_card.status != "COMPLETED":
        raise ValueError(
            "An invoice can only be generated for a completed job card."
        )

    existing_invoice = (
        db.query(Invoice)
        .filter(Invoice.job_card_id == job_card_id)
        .first()
    )

    if existing_invoice:
        raise ValueError(
            "An invoice already exists for this job card."
        )

    costs = calculate_job_card_costs(job_card)

    invoice_number = (
        f"INV-{datetime.now(timezone.utc):%Y%m%d}-"
        f"{uuid4().hex[:8].upper()}"
    )

    invoice = Invoice(
        invoice_number=invoice_number,
        job_card_id=job_card_id,
        subtotal=costs["subtotal"],
        tax_amount=costs["tax_amount"],
        total_amount=costs["total_amount"],
        status="UNPAID",
        issued_at=datetime.now(timezone.utc),
        due_at=None
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice

def get_invoice(db: Session, invoice_id: int) -> Invoice | None:
    return (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .first()
    )


def get_job_card_invoice(
    db: Session,
    job_card_id: int
) -> Invoice | None:
    return (
        db.query(Invoice)
        .filter(Invoice.job_card_id == job_card_id)
        .first()
    )


def get_all_invoices(db: Session) -> list[Invoice]:
    return (
        db.query(Invoice)
        .order_by(Invoice.issued_at.desc())
        .all()
    )