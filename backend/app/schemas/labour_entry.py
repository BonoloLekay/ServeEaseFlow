from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LabourEntryCreate(BaseModel):
    job_card_id: int = Field(gt=0)
    technician_id: int = Field(gt=0)
    description: str = Field(min_length=3, max_length=2000)
    hours_worked: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    hourly_rate: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class LabourEntryUpdate(BaseModel):
    description: str | None = Field(
        default=None,
        min_length=3,
        max_length=2000
    )
    hours_worked: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=8,
        decimal_places=2
    )
    hourly_rate: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2
    )


class LabourEntryResponse(BaseModel):
    id: int
    job_card_id: int
    technician_id: int
    description: str
    hours_worked: Decimal
    hourly_rate: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
