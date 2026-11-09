from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceBayCreate(BaseModel):
    bay_number: str = Field(
        min_length=1,
        max_length=20
    )

    description: str | None = Field(
        default=None,
        max_length=255
    )


class ServiceBayUpdate(BaseModel):
    bay_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=20
    )

    description: str | None = Field(
        default=None,
        max_length=255
    )

    is_active: bool | None = None


class ServiceBayResponse(BaseModel):
    id: int
    bay_number: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)