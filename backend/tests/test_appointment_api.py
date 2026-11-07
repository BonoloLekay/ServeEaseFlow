
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import ServiceCategory


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


def create_test_customer(client):
    email = f"appointment_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Appointment",
            "last_name": "Tester",
            "email": email,
            "phone_number": "0712345678",
            "password": "TestPassword123!"
        }
    )

    assert registration.status_code in (200, 201)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!"
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "email": email,
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }


def create_test_vehicle(client, customer):
    response = client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"APT{uuid.uuid4().hex[:6].upper()}",
            "vin": uuid.uuid4().hex[:17].upper(),
            "make": "BMW",
            "model": "320i",
            "year": 2023,
            "colour": "Black"
        }
    )

    assert response.status_code == 201

    return response.json()


def create_test_service_category(db):
    category = ServiceCategory(
        name=f"Test Service {uuid.uuid4().hex[:8]}",
        description="Appointment API test service",
        base_price=500.00,
        estimated_duration_hours=1.50,
        is_active=True
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def future_appointment_date(days=7):
    return (
        datetime.now(timezone.utc) + timedelta(days=days)
    ).isoformat()


def create_test_appointment(client, db, customer):
    vehicle = create_test_vehicle(client, customer)
    category = create_test_service_category(db)

    response = client.post(
        "/api/v1/appointments/",
        headers=customer["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "service_category_id": category.id,
            "scheduled_at": future_appointment_date(),
            "customer_notes": "Please inspect the brakes."
        }
    )

    assert response.status_code == 201

    return response.json()


def test_create_appointment(client, db):
    customer = create_test_customer(client)

    appointment = create_test_appointment(
        client,
        db,
        customer
    )

    assert appointment["booking_reference"].startswith("SE-")
    assert appointment["status"] == "PENDING"
    assert appointment["customer_notes"] == "Please inspect the brakes."


def test_list_customer_appointments(client, db):
    customer = create_test_customer(client)

    create_test_appointment(client, db, customer)

    response = client.get(
        "/api/v1/appointments/",
        headers=customer["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_customer_appointment(client, db):
    customer = create_test_customer(client)

    appointment = create_test_appointment(
        client,
        db,
        customer
    )

    response = client.get(
        f"/api/v1/appointments/{appointment['id']}",
        headers=customer["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == appointment["id"]


def test_update_appointment(client, db):
    customer = create_test_customer(client)

    appointment = create_test_appointment(
        client,
        db,
        customer
    )

    response = client.put(
        f"/api/v1/appointments/{appointment['id']}",
        headers=customer["headers"],
        json={
            "scheduled_at": future_appointment_date(days=14),
            "customer_notes": "Please inspect the engine."
        }
    )

    assert response.status_code == 200
    assert response.json()["customer_notes"] == "Please inspect the engine."


def test_cancel_appointment(client, db):
    customer = create_test_customer(client)

    appointment = create_test_appointment(
        client,
        db,
        customer
    )

    response = client.delete(
        f"/api/v1/appointments/{appointment['id']}",
        headers=customer["headers"]
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_customer_cannot_access_another_customers_appointment(client, db):
    customer_one = create_test_customer(client)
    customer_two = create_test_customer(client)

    appointment = create_test_appointment(
        client,
        db,
        customer_one
    )

    response = client.get(
        f"/api/v1/appointments/{appointment['id']}",
        headers=customer_two["headers"]
    )

    assert response.status_code == 404


def test_create_appointment_with_invalid_vehicle(client, db):
    customer = create_test_customer(client)
    category = create_test_service_category(db)

    response = client.post(
        "/api/v1/appointments/",
        headers=customer["headers"],
        json={
            "vehicle_id": 999999,
            "service_category_id": category.id,
            "scheduled_at": future_appointment_date()
        }
    )

    assert response.status_code == 400


def test_create_appointment_with_invalid_service_category(client):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)

    response = client.post(
        "/api/v1/appointments/",
        headers=customer["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "service_category_id": 999999,
            "scheduled_at": future_appointment_date()
        }
    )

    assert response.status_code == 400


def test_create_appointment_with_past_date(client, db):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)
    category = create_test_service_category(db)

    past_date = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()

    response = client.post(
        "/api/v1/appointments/",
        headers=customer["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "service_category_id": category.id,
            "scheduled_at": past_date
        }
    )

    assert response.status_code == 400


def test_cancelled_appointment_cannot_be_updated(client, db):
    customer = create_test_customer(client)

    appointment = create_test_appointment(
        client,
        db,
        customer
    )

    cancellation = client.delete(
        f"/api/v1/appointments/{appointment['id']}",
        headers=customer["headers"]
    )

    assert cancellation.status_code == 200

    response = client.put(
        f"/api/v1/appointments/{appointment['id']}",
        headers=customer["headers"],
        json={
            "customer_notes": "Attempted update after cancellation."
        }
    )

    assert response.status_code == 400
