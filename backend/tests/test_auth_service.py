
import uuid

import pytest

from app.db.session import SessionLocal
from app.models import User, Customer
from app.schemas.auth import CustomerRegister
from app.services.auth_service import (
    register_customer,
    authenticate_customer
)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def test_customer_registration(db):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    customer_data = CustomerRegister(
        first_name="Test",
        last_name="Customer",
        email=email,
        phone_number="0712345678",
        password="TestPassword123!"
    )

    customer = register_customer(db, customer_data)

    assert customer.id is not None
    assert customer.customer_number.startswith("SE-")
    assert customer.user.email == email

    db.delete(customer)
    db.delete(customer.user)
    db.commit()


def test_duplicate_email_registration_is_rejected(db):
    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"

    customer_data = CustomerRegister(
        first_name="Test",
        last_name="Customer",
        email=email,
        phone_number="0712345678",
        password="TestPassword123!"
    )

    customer = register_customer(db, customer_data)

    with pytest.raises(ValueError, match="already registered"):
        register_customer(db, customer_data)

    db.delete(customer)
    db.delete(customer.user)
    db.commit()


def test_customer_login_success(db):
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"

    customer_data = CustomerRegister(
        first_name="Login",
        last_name="Test",
        email=email,
        phone_number="0712345678",
        password="TestPassword123!"
    )

    customer = register_customer(db, customer_data)

    authenticated_user = authenticate_customer(
        db,
        email,
        "TestPassword123!"
    )

    assert authenticated_user is not None
    assert authenticated_user.email == email

    db.delete(customer)
    db.delete(customer.user)
    db.commit()


def test_customer_login_wrong_password(db):
    email = f"wrong_{uuid.uuid4().hex[:8]}@example.com"

    customer_data = CustomerRegister(
        first_name="Wrong",
        last_name="Password",
        email=email,
        phone_number="0712345678",
        password="TestPassword123!"
    )

    customer = register_customer(db, customer_data)

    authenticated_user = authenticate_customer(
        db,
        email,
        "WrongPassword123!"
    )

    assert authenticated_user is None

    db.delete(customer)
    db.delete(customer.user)
    db.commit()


def test_inactive_customer_login_is_rejected(db):
    email = f"inactive_{uuid.uuid4().hex[:8]}@example.com"

    customer_data = CustomerRegister(
        first_name="Inactive",
        last_name="Customer",
        email=email,
        phone_number="0712345678",
        password="TestPassword123!"
    )

    customer = register_customer(db, customer_data)

    customer.user.is_active = False
    db.commit()

    authenticated_user = authenticate_customer(
        db,
        email,
        "TestPassword123!"
    )

    assert authenticated_user is None

    db.delete(customer)
    db.delete(customer.user)
    db.commit()
