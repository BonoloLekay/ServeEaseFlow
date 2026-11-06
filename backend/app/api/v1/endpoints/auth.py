from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    CustomerRegister,
    CustomerRegisterResponse,
    LoginRequest,
    CustomerLoginResponse
)
from app.services.auth_service import (
    register_customer,
    authenticate_customer
)

from app.core.security import create_access_token
from app.core.dependencies import get_current_user, require_roles
from app.models import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=CustomerRegisterResponse,
    status_code=status.HTTP_201_CREATED
)
def customer_registration(
    customer_data: CustomerRegister,
    db: Session = Depends(get_db)
):
    try:
        customer = register_customer(db, customer_data)

        return {
            "id": customer.id,
            "customer_number": customer.customer_number,
            "first_name": customer.user.first_name,
            "last_name": customer.user.last_name,
            "email": customer.user.email,
            "message": "Customer registered successfully."
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer registration failed."
        )


from app.core.security import create_access_token


@router.post(
    "/login",
    response_model=CustomerLoginResponse
)
def customer_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_customer(
        db,
        login_data.email,
        login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "customer_number": user.customer.customer_number,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }


@router.get("/me")
def get_customer_profile(
    current_user: User = Depends(require_roles("CUSTOMER"))
):
    return {
        "customer_number": current_user.customer.customer_number,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number
    }