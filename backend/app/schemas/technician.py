from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field
)


class TechnicianCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)

    employee_number: str = Field(min_length=2, max_length=30)
    specialization: str | None = Field(default=None, max_length=100)


class TechnicianUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)

    specialization: str | None = Field(default=None, max_length=100)
    is_available: bool | None = None


class TechnicianUserResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str | None

    model_config = ConfigDict(from_attributes=True)


class TechnicianResponse(BaseModel):
    id: int
    user_id: int
    employee_number: str
    specialization: str | None
    is_available: bool
    created_at: datetime

    user: TechnicianUserResponse

    model_config = ConfigDict(from_attributes=True)