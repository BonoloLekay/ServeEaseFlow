
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobAssignmentCreate(BaseModel):
    job_card_id: int = Field(gt=0)
    technician_id: int = Field(gt=0)
    service_bay_id: int = Field(gt=0)


class JobAssignmentStatusUpdate(BaseModel):
    status: str = Field(
        min_length=3,
        max_length=30
    )


class JobAssignmentResponse(BaseModel):
    id: int
    job_card_id: int
    technician_id: int
    service_bay_id: int
    status: str
    assigned_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
