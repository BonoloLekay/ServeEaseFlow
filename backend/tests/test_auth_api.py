import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import User


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def delete_test_user(db, email):
    user = db.query(User).filter(User.email == email).first()

    if user:
        if user.customer:
            db.delete(user.customer)

        db.delete(user)
        db.commit()


def test_customer_registration_endpoint(client, db):
    email = f"api_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "API",
            "last_name": "Tester",
            "email": email,
            "phone_number": "0712345678",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code in (200, 201)
    assert response.json()["email"] == email
    assert response.json()["customer_number"].startswith("SE-")

    delete_test_user(db, email)


def test_duplicate_registration_endpoint(client, db):
    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"

    data = {
        "first_name": "API",
        "last_name": "Tester",
        "email": email,
        "phone_number": "0712345678",
        "password": "TestPassword123!"
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=data
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=data
    )

    assert first_response.status_code in (200, 201)
    assert second_response.status_code == 409

    delete_test_user(db, email)


def test_customer_login_endpoint(client, db):
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Login",
            "last_name": "Tester",
            "email": email,
            "phone_number": "0712345678",
            "password": "TestPassword123!"
        }
    )

    assert registration.status_code in (200, 201)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200
    assert response.json()["access_token"]

    delete_test_user(db, email)


def test_login_rejects_wrong_password(client, db):
    email = f"wrong_{uuid.uuid4().hex[:8]}@example.com"

    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Wrong",
            "last_name": "Password",
            "email": email,
            "phone_number": "0712345678",
            "password": "TestPassword123!"
        }
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401

    delete_test_user(db, email)


def test_customer_profile_requires_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401