from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    registration_number: str = Field(
        min_length=2,
        max_length=20
    )
    vin: str | None = Field(
        default=None,
        min_length=5,
        max_length=50
    )
    make: str = Field(min_length=2, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2100)
    colour: str | None = Field(
        default=None,
        max_length=50
    )


class VehicleUpdate(BaseModel):
    registration_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=20
    )
    vin: str | None = Field(
        default=None,
        min_length=5,
        max_length=50
    )
    make: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    year: int | None = Field(
        default=None,
        ge=1900,
        le=2100
    )
    colour: str | None = Field(
        default=None,
        max_length=50
    )


class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    vin: str | None
    make: str
    model: str
    year: int
    colour: str | None

    model_config = ConfigDict(from_attributes=True)