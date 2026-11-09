from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    job_card_id: int
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    issued_at: datetime
    due_at: datetime | None

    model_config = ConfigDict(from_attributes=True)