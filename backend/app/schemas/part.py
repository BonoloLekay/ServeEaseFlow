
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PartCreate(BaseModel):
    part_number: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None

    quantity_in_stock: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=5, ge=0)

    unit_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    selling_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class PartUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None

    reorder_level: int | None = Field(default=None, ge=0)

    unit_cost: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    selling_price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )

    is_active: bool | None = None


class StockMovementCreate(BaseModel):
    quantity: int = Field(gt=0)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class JobCardPartCreate(BaseModel):
    part_id: int = Field(gt=0)
    quantity_used: int = Field(gt=0)


class InventoryTransactionResponse(BaseModel):
    id: int
    part_id: int
    transaction_type: str
    quantity: int
    reference: str | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PartResponse(BaseModel):
    id: int
    part_number: str
    name: str
    description: str | None
    quantity_in_stock: int
    reorder_level: int
    unit_cost: Decimal
    selling_price: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCardPartResponse(BaseModel):
    id: int
    job_card_id: int
    part_id: int
    quantity_used: int
    unit_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
