
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    invoice_id: int = Field(gt=0)


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    payment_reference: str
    payfast_transaction_id: str | None
    amount: Decimal
    payment_method: str
    status: str
    paid_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaymentCheckoutResponse(PaymentResponse):
    checkout_url: str
    form_fields: dict[str, str]