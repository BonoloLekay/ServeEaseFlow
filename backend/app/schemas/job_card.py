from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCardCreate(BaseModel):
    appointment_id: int | None = Field(
        default=None,
        gt=0
    )

    vehicle_id: int = Field(gt=0)

    reported_issue: str = Field(
        min_length=3,
        max_length=5000
    )

    odometer_reading: int | None = Field(
        default=None,
        ge=0
    )


class JobCardUpdate(BaseModel):
    reported_issue: str | None = Field(
        default=None,
        min_length=3,
        max_length=5000
    )

    diagnosis: str | None = Field(
        default=None,
        max_length=5000
    )

    work_performed: str | None = Field(
        default=None,
        max_length=5000
    )

    odometer_reading: int | None = Field(
        default=None,
        ge=0
    )


class JobCardStatusUpdate(BaseModel):
    status: str = Field(
        min_length=3,
        max_length=30
    )


class JobCardResponse(BaseModel):
    id: int
    job_card_number: str
    appointment_id: int | None
    vehicle_id: int
    reported_issue: str
    diagnosis: str | None
    work_performed: str | None
    odometer_reading: int | None
    status: str
    checked_in_at: datetime
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)