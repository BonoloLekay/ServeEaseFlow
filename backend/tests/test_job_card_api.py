import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import Role, User
from app.core.security import hash_password, create_access_token


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


def create_test_staff(db, role_name):
    role = db.query(Role).filter(
        Role.name == role_name
    ).first()

    if not role:
        role = Role(
            name=role_name,
            description=f"{role_name} test role"
        )
        db.add(role)
        db.commit()
        db.refresh(role)

    user = User(
        role_id=role.id,
        email=f"{role_name.lower()}_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPassword123!"),
        first_name="Test",
        last_name=role_name.title()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        subject=str(user.id)
    )

    return {
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }


def create_test_customer(client):
    email = f"jobcard_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "JobCard",
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

    return {
        "headers": {
            "Authorization": (
                f"Bearer {login.json()['access_token']}"
            )
        }
    }


def create_test_vehicle(client, customer):
    response = client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"JC{uuid.uuid4().hex[:6].upper()}",
            "vin": uuid.uuid4().hex[:17].upper(),
            "make": "BMW",
            "model": "320i",
            "year": 2023,
            "colour": "Black"
        }
    )

    assert response.status_code == 201

    return response.json()


def create_test_job_card(client, db, staff):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)

    response = client.post(
        "/api/v1/job-cards/",
        headers=staff["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "reported_issue": "Engine warning light is on.",
            "odometer_reading": 45000
        }
    )

    assert response.status_code == 201

    return response.json()


def test_admin_can_create_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(
        client,
        db,
        admin
    )

    assert job_card["job_card_number"].startswith("JC-")
    assert job_card["status"] == "OPEN"
    assert job_card["reported_issue"] == (
        "Engine warning light is on."
    )


def test_reception_can_create_job_card(client, db):
    reception = create_test_staff(db, "RECEPTION")

    job_card = create_test_job_card(
        client,
        db,
        reception
    )

    assert job_card["status"] == "OPEN"


def test_customer_cannot_create_job_card(client, db):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)

    response = client.post(
        "/api/v1/job-cards/",
        headers=customer["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "reported_issue": "Brake inspection required."
        }
    )

    assert response.status_code == 403


def test_list_job_cards(client, db):
    admin = create_test_staff(db, "ADMIN")

    created_job_card = create_test_job_card(
        client,
        db,
        admin
    )

    response = client.get(
        "/api/v1/job-cards/",
        headers=admin["headers"]
    )

    assert response.status_code == 200

    job_cards = response.json()

    assert len(job_cards) >= 1

    job_card_ids = [
        job_card["id"]
        for job_card in job_cards
    ]

    assert created_job_card["id"] in job_card_ids


def test_get_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(
        client,
        db,
        admin
    )

    response = client.get(
        f"/api/v1/job-cards/{job_card['id']}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == job_card["id"]


def test_update_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(
        client,
        db,
        admin
    )

    response = client.put(
        f"/api/v1/job-cards/{job_card['id']}",
        headers=admin["headers"],
        json={
            "diagnosis": "Faulty ignition coil.",
            "work_performed": "Initial diagnostic inspection."
        }
    )

    assert response.status_code == 200
    assert response.json()["diagnosis"] == "Faulty ignition coil."


def test_update_job_card_status(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(
        client,
        db,
        admin
    )

    response = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=admin["headers"],
        json={
            "status": "IN_PROGRESS"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_invalid_job_card_status_transition(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(
        client,
        db,
        admin
    )

    response = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=admin["headers"],
        json={
            "status": "COMPLETED"
        }
    )

    assert response.status_code == 400


def test_job_card_not_found(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/job-cards/999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404