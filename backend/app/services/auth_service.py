import uuid

from sqlalchemy.orm import Session

from app.models import User, Customer, Role
from app.core.security import hash_password, verify_password
from app.schemas.auth import CustomerRegister


def register_customer(
    db: Session,
    customer_data: CustomerRegister
):
    # Check whether the email already exists
    existing_user = db.query(User).filter(
        User.email == customer_data.email
    ).first()

    if existing_user:
        raise ValueError("Email address is already registered.")

    # Find the CUSTOMER role
    customer_role = db.query(Role).filter(
        Role.name == "CUSTOMER"
    ).first()

    if not customer_role:
        raise ValueError("CUSTOMER role does not exist.")

    try:
        # Create user account
        new_user = User(
            role_id=customer_role.id,
            email=customer_data.email,
            password_hash=hash_password(customer_data.password),
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            phone_number=customer_data.phone_number
        )

        db.add(new_user)
        db.flush()

        # Generate customer number
        customer_number = f"SE-{uuid.uuid4().hex[:10].upper()}"

        # Create customer profile
        new_customer = Customer(
            user_id=new_user.id,
            customer_number=customer_number
        )

        db.add(new_customer)

        db.commit()
        db.refresh(new_customer)

        return new_customer

    except Exception:
        db.rollback()
        raise

def authenticate_customer(
    db: Session,
    email: str,
    password: str
):
    user = db.query(User).filter(
        User.email == email
    ).first()

    # Reject invalid credentials
    if not user or not verify_password(
        password,
        user.password_hash
    ):
        return None

    # Reject inactive accounts
    if not user.is_active:
        return None

    # Allow customer accounts only
    if user.role.name != "CUSTOMER":
        return None

    return user