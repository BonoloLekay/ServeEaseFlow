
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import (
    Role,
    User,
    Technician,
    ServiceBay
)
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
        "user": user,
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }


def create_test_customer(client):
    email = f"assignment_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Assignment",
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
            "registration_number": f"JA{uuid.uuid4().hex[:6].upper()}",
            "vin": uuid.uuid4().hex[:17].upper(),
            "make": "BMW",
            "model": "320i",
            "year": 2023,
            "colour": "Black"
        }
    )

    assert response.status_code == 201

    return response.json()


def create_test_job_card(client, admin):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)

    response = client.post(
        "/api/v1/job-cards/",
        headers=admin["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "reported_issue": "Engine inspection required.",
            "odometer_reading": 45000
        }
    )

    assert response.status_code == 201

    return response.json()


def create_test_technician(db):
    staff = create_test_staff(db, "TECHNICIAN")

    technician = Technician(
        user_id=staff["user"].id,
        employee_number=f"TECH-{uuid.uuid4().hex[:8].upper()}",
        specialization="General Maintenance",
        is_available=True
    )

    db.add(technician)
    db.commit()
    db.refresh(technician)

    return technician


def create_test_service_bay(db):
    service_bay = ServiceBay(
        bay_number=f"BAY-{uuid.uuid4().hex[:8].upper()}",
        description="General service bay",
        is_active=True
    )

    db.add(service_bay)
    db.commit()
    db.refresh(service_bay)

    return service_bay


def create_test_assignment(
    client,
    admin,
    job_card,
    technician,
    service_bay
):
    response = client.post(
        "/api/v1/job-assignments/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician.id,
            "service_bay_id": service_bay.id
        }
    )

    return response


def test_admin_can_create_job_assignment(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    response = create_test_assignment(
        client,
        admin,
        job_card,
        technician,
        service_bay
    )

    assert response.status_code == 201
    assert response.json()["job_card_id"] == job_card["id"]
    assert response.json()["technician_id"] == technician.id
    assert response.json()["service_bay_id"] == service_bay.id
    assert response.json()["status"] == "ASSIGNED"


def test_reception_can_create_job_assignment(client, db):
    reception = create_test_staff(db, "RECEPTION")
    job_card = create_test_job_card(client, reception)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    response = create_test_assignment(
        client,
        reception,
        job_card,
        technician,
        service_bay
    )

    assert response.status_code == 201


def test_customer_cannot_create_job_assignment(client, db):
    admin = create_test_staff(db, "ADMIN")
    customer = create_test_customer(client)

    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    response = client.post(
        "/api/v1/job-assignments/",
        headers=customer["headers"],
        json={
            "job_card_id": job_card["id"],
            "technician_id": technician.id,
            "service_bay_id": service_bay.id
        }
    )

    assert response.status_code == 403


def test_list_job_assignments(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    created = create_test_assignment(
        client,
        admin,
        job_card,
        technician,
        service_bay
    )

    assert created.status_code == 201

    response = client.get(
        "/api/v1/job-assignments/",
        headers=admin["headers"]
    )

    assert response.status_code == 200

    assignment_ids = [
        assignment["id"]
        for assignment in response.json()
    ]

    assert created.json()["id"] in assignment_ids


def test_get_job_assignment(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    created = create_test_assignment(
        client,
        admin,
        job_card,
        technician,
        service_bay
    )

    response = client.get(
        f"/api/v1/job-assignments/{created.json()['id']}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]


def test_technician_cannot_have_conflicting_assignments(client, db):
    admin = create_test_staff(db, "ADMIN")

    first_job = create_test_job_card(client, admin)
    second_job = create_test_job_card(client, admin)

    technician = create_test_technician(db)
    first_bay = create_test_service_bay(db)
    second_bay = create_test_service_bay(db)

    first_assignment = create_test_assignment(
        client,
        admin,
        first_job,
        technician,
        first_bay
    )

    assert first_assignment.status_code == 201

    second_assignment = create_test_assignment(
        client,
        admin,
        second_job,
        technician,
        second_bay
    )

    assert second_assignment.status_code == 400
    assert "Technician already has an active" in (
        second_assignment.json()["detail"]
    )


def test_service_bay_cannot_have_conflicting_assignments(client, db):
    admin = create_test_staff(db, "ADMIN")

    first_job = create_test_job_card(client, admin)
    second_job = create_test_job_card(client, admin)

    first_technician = create_test_technician(db)
    second_technician = create_test_technician(db)

    service_bay = create_test_service_bay(db)

    first_assignment = create_test_assignment(
        client,
        admin,
        first_job,
        first_technician,
        service_bay
    )

    assert first_assignment.status_code == 201

    second_assignment = create_test_assignment(
        client,
        admin,
        second_job,
        second_technician,
        service_bay
    )

    assert second_assignment.status_code == 400
    assert "Service bay already has an active" in (
        second_assignment.json()["detail"]
    )


def test_update_job_assignment_status(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    created = create_test_assignment(
        client,
        admin,
        job_card,
        technician,
        service_bay
    )

    assignment_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/job-assignments/{assignment_id}/status",
        headers=admin["headers"],
        json={"status": "IN_PROGRESS"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"
    assert response.json()["started_at"] is not None


def test_invalid_job_assignment_status_transition(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)
    technician = create_test_technician(db)
    service_bay = create_test_service_bay(db)

    created = create_test_assignment(
        client,
        admin,
        job_card,
        technician,
        service_bay
    )

    response = client.patch(
        f"/api/v1/job-assignments/{created.json()['id']}/status",
        headers=admin["headers"],
        json={"status": "COMPLETED"}
    )

    assert response.status_code == 400


def test_job_assignment_not_found(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/job-assignments/999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404
