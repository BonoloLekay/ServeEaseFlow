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



def create_test_customer(client):
    email = f"vehicle_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Vehicle",
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


def test_create_vehicle(client):
    customer = create_test_customer(client)

    response = client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"TEST{uuid.uuid4().hex[:6].upper()}",
            "vin": f"TESTVIN{uuid.uuid4().hex[:10].upper()}",
            "make": "BMW",
            "model": "320i",
            "year": 2022,
            "colour": "Black"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["registration_number"].startswith("TEST")
    assert data["make"] == "BMW"
    assert data["model"] == "320i"
    assert data["year"] == 2022


def test_list_customer_vehicles(client):
    customer = create_test_customer(client)

    client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"LIST{uuid.uuid4().hex[:6].upper()}",
            "vin": f"LISTVIN{uuid.uuid4().hex[:10].upper()}",
            "make": "BMW",
            "model": "X3",
            "year": 2023,
            "colour": "Blue"
        }
    )

    response = client.get(
        "/api/v1/vehicles/",
        headers=customer["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["model"] == "X3"

def test_update_vehicle(client):
    customer = create_test_customer(client)

    creation = client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"UPD{uuid.uuid4().hex[:6].upper()}",
            "vin": f"UPDVIN{uuid.uuid4().hex[:10].upper()}",
            "make": "BMW",
            "model": "320i",
            "year": 2022,
            "colour": "Black"
        }
    )

    vehicle_id = creation.json()["id"]

    response = client.put(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=customer["headers"],
        json={"colour": "White"}
    )

    assert response.status_code == 200
    assert response.json()["colour"] == "White"

def test_delete_vehicle(client):
    customer = create_test_customer(client)

    creation = client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"DEL{uuid.uuid4().hex[:6].upper()}",
            "vin": f"DELVIN{uuid.uuid4().hex[:10].upper()}",
            "make": "BMW",
            "model": "X5",
            "year": 2024,
            "colour": "Black"
        }
    )

    vehicle_id = creation.json()["id"]

    response = client.delete(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=customer["headers"]
    )

    assert response.status_code == 204

    retrieval = client.get(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=customer["headers"]
    )

    assert retrieval.status_code == 404

def test_customer_cannot_access_another_customers_vehicle(client):
    customer_one = create_test_customer(client)
    customer_two = create_test_customer(client)

    creation = client.post(
        "/api/v1/vehicles/",
        headers=customer_one["headers"],
        json={
            "registration_number": f"ISO{uuid.uuid4().hex[:6].upper()}",
            "vin": f"ISOVIN{uuid.uuid4().hex[:10].upper()}",
            "make": "BMW",
            "model": "M3",
            "year": 2023,
            "colour": "Red"
        }
    )

    vehicle_id = creation.json()["id"]

    response = client.get(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=customer_two["headers"]
    )

    assert response.status_code == 404