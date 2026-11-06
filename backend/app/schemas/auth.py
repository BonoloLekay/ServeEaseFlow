from pydantic import BaseModel, EmailStr, Field


class CustomerRegister(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CustomerRegisterResponse(BaseModel):
    id: int
    customer_number: str
    first_name: str
    last_name: str
    email: EmailStr
    message: str

class CustomerLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_number: str
    first_name: str
    last_name: str
    email: EmailStr