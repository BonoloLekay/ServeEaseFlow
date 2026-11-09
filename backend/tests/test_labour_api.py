
import uuid
from decimal import Decimal

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

    token = create_access_token(subject=str(user.id))

    return {
        "user": user,
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }


def create_test_customer(client):
    email = f"labour_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Labour",
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
            "Authorization": f"Bearer {login.json()['access_token']}"
        }
    }


def create_test_vehicle(client, customer):
    response = client.post(
        "/api/v1/vehicles/",
        headers=customer["headers"],
        json={
            "registration_number": f"LB{uuid.uuid4().hex[:6].upper()}",
            "vin": uuid.uuid4().hex[:17].upper(),
            "make": "BMW",
            "model": "320i",
            "year": 2023,
            "colour": "Black"
        }
    )

    assert response.status_code == 201
    return response.json()


def create_test_job_card(client, staff):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)

    response = client.post(
        "/api/v1/job-cards/",
        headers=staff["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "reported_issue": "Engine inspection required.",
            "odometer_reading": 45000
        }
    )

    assert response.status_code == 201
    return response.json()


def create_test_technician(client, staff):
    response = client.post(
        "/api/v1/technicians/",
        headers=staff["headers"],
        json={
            "email": f"tech_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "Technician",
            "phone_number": "0712345678",
            "employee_number": f"TECH-{uuid.uuid4().hex[:8].upper()}",
            "specialization": "Engine Diagnostics"
        }
    )

    assert response.status_code == 201
    return response.json()


def test_admin_can_create_labour_entry(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    response = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Engine diagnostics and inspection",
            "hours_worked": "2.50",
            "hourly_rate": "650.00"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_card_id"] == job_card["id"]
    assert data["technician_id"] == technician["id"]
    assert data["description"] == "Engine diagnostics and inspection"
    assert Decimal(data["hours_worked"]) == Decimal("2.50")
    assert Decimal(data["hourly_rate"]) == Decimal("650.00")


def test_job_card_supports_multiple_labour_entries(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)

    technician_one = create_test_technician(client, admin)
    technician_two = create_test_technician(client, admin)

    for technician, hours, rate in [
        (technician_one, "2.00", "500.00"),
        (technician_two, "1.50", "600.00")
    ]:
        response = client.post(
            "/api/v1/labour/",
            headers=admin["headers"],
            json={
                "job_card_id": job_card["id"],
                "technician_id": technician["id"],
                "description": "Vehicle servicing",
                "hours_worked": hours,
                "hourly_rate": rate
            }
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/v1/labour/job-cards/{job_card['id']}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) == 2



def test_calculate_job_card_labour_total(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)

    technician_one = create_test_technician(client, admin)
    technician_two = create_test_technician(client, admin)

    entries = [
        (technician_one, "2.00", "500.00"),
        (technician_two, "1.50", "600.00")
    ]

    for technician, hours, rate in entries:
        response = client.post(
            "/api/v1/labour/",
            headers=admin["headers"],
            json={
                "job_card_id": job_card["id"],
                "technician_id": technician["id"],
                "description": "Vehicle servicing",
                "hours_worked": hours,
                "hourly_rate": rate
            }
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/v1/labour/job-cards/{job_card['id']}/total",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert Decimal(response.json()["labour_total"]) == Decimal("1900.00")



def test_reception_can_create_labour_entry(client, db):
    reception = create_test_staff(db, "RECEPTION")

    job_card = create_test_job_card(client, reception)
    technician = create_test_technician(client, reception)

    response = client.post(
        "/api/v1/labour/",
        headers=reception["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Brake inspection",
            "hours_worked": "1.00",
            "hourly_rate": "450.00"
        }
    )

    assert response.status_code == 201


def test_customer_cannot_create_labour_entry(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    customer = create_test_customer(client)

    response = client.post(
        "/api/v1/labour/",
        headers=customer["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Engine inspection",
            "hours_worked": "2.00",
            "hourly_rate": "500.00"
        }
    )

    assert response.status_code == 403



def test_admin_can_update_labour_entry(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    created = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Initial inspection",
            "hours_worked": "2.00",
            "hourly_rate": "500.00"
        }
    )

    assert created.status_code == 201

    entry_id = created.json()["id"]

    response = client.put(
        f"/api/v1/labour/{entry_id}",
        headers=admin["headers"],
        json={
            "description": "Completed engine diagnostics",
            "hours_worked": "3.00"
        }
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Completed engine diagnostics"
    assert Decimal(response.json()["hours_worked"]) == Decimal("3.00")


def test_labour_entry_rejects_invalid_hours(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    response = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Engine inspection",
            "hours_worked": "0",
            "hourly_rate": "500.00"
        }
    )

    assert response.status_code == 422


def test_labour_entry_rejects_invalid_hourly_rate(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    response = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Engine inspection",
            "hours_worked": "2.00",
            "hourly_rate": "0"
        }
    )

    assert response.status_code == 422


def test_labour_entries_return_404_for_missing_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/labour/job-cards/999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404


def test_labour_entry_returns_404_for_missing_technician(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)

    response = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": 999999,
            "description": "Engine inspection",
            "hours_worked": "2.00",
            "hourly_rate": "500.00"
        }
    )

    assert response.status_code == 404


def test_cannot_add_labour_to_completed_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    in_progress = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=admin["headers"],
        json={"status": "IN_PROGRESS"}
    )

    assert in_progress.status_code == 200

    completed = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=admin["headers"],
        json={"status": "COMPLETED"}
    )

    assert completed.status_code == 200

    response = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Additional engine inspection",
            "hours_worked": "1.00",
            "hourly_rate": "500.00"
        }
    )

    assert response.status_code == 400


def test_cannot_update_labour_on_completed_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(client, admin)

    created = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician["id"],
            "description": "Engine inspection",
            "hours_worked": "2.00",
            "hourly_rate": "500.00"
        }
    )

    assert created.status_code == 201

    entry_id = created.json()["id"]

    client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=admin["headers"],
        json={"status": "IN_PROGRESS"}
    )

    completed = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=admin["headers"],
        json={"status": "COMPLETED"}
    )

    assert completed.status_code == 200

    response = client.put(
        f"/api/v1/labour/{entry_id}",
        headers=admin["headers"],
        json={"hours_worked": "3.00"}
    )

    assert response.status_code == 400


def test_update_missing_labour_entry_returns_404(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.put(
        "/api/v1/labour/999999",
        headers=admin["headers"],
        json={"hours_worked": "3.00"}
    )

    assert response.status_code == 404
