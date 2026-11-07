from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    service_category_id: int = Field(gt=0)
    scheduled_at: datetime
    customer_notes: str | None = Field(
        default=None,
        max_length=2000
    )


class AppointmentUpdate(BaseModel):
    vehicle_id: int | None = Field(default=None, gt=0)
    service_category_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime | None = None
    customer_notes: str | None = Field(
        default=None,
        max_length=2000
    )


class AppointmentResponse(BaseModel):
    id: int
    booking_reference: str
    vehicle_id: int
    service_category_id: int
    scheduled_at: datetime
    status: str
    customer_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)