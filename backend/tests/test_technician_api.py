
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import Role, User, Technician
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


def create_test_technician(client, headers):
    return client.post(
        "/api/v1/technicians/",
        headers=headers,
        json={
            "email": f"technician_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "Technician",
            "phone_number": "0712345678",
            "employee_number": f"TECH-{uuid.uuid4().hex[:8].upper()}",
            "specialization": "Engine Diagnostics"
        }
    )


def test_admin_can_create_technician(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = create_test_technician(
        client,
        admin["headers"]
    )

    assert response.status_code == 201
    assert response.json()["employee_number"].startswith("TECH-")
    assert response.json()["user"]["email"]
    assert response.json()["is_available"] is True

    assert "password_hash" not in response.json()
    assert "password" not in response.json()


def test_reception_can_create_technician(client, db):
    reception = create_test_staff(db, "RECEPTION")

    response = create_test_technician(
        client,
        reception["headers"]
    )

    assert response.status_code == 201


def test_customer_cannot_create_technician(client, db):
    customer = create_test_staff(db, "CUSTOMER")

    response = create_test_technician(
        client,
        customer["headers"]
    )

    assert response.status_code == 403


def test_duplicate_email_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"

    first_response = client.post(
        "/api/v1/technicians/",
        headers=admin["headers"],
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "First",
            "last_name": "Technician",
            "employee_number": f"TECH-{uuid.uuid4().hex[:8].upper()}"
        }
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/technicians/",
        headers=admin["headers"],
        json={
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Second",
            "last_name": "Technician",
            "employee_number": f"TECH-{uuid.uuid4().hex[:8].upper()}"
        }
    )

    assert second_response.status_code == 400
    assert "Email address is already registered" in (
        second_response.json()["detail"]
    )


def test_duplicate_employee_number_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    employee_number = f"TECH-{uuid.uuid4().hex[:8].upper()}"

    first_response = client.post(
        "/api/v1/technicians/",
        headers=admin["headers"],
        json={
            "email": f"first_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "first_name": "First",
            "last_name": "Technician",
            "employee_number": employee_number
        }
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/technicians/",
        headers=admin["headers"],
        json={
            "email": f"second_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "first_name": "Second",
            "last_name": "Technician",
            "employee_number": employee_number
        }
    )

    assert second_response.status_code == 400
    assert "Employee number is already registered" in (
        second_response.json()["detail"]
    )


def test_list_technicians(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_technician(
        client,
        admin["headers"]
    )

    assert created.status_code == 201

    response = client.get(
        "/api/v1/technicians/",
        headers=admin["headers"]
    )

    assert response.status_code == 200

    technician_ids = [
        technician["id"]
        for technician in response.json()
    ]

    assert created.json()["id"] in technician_ids


def test_get_technician(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_technician(
        client,
        admin["headers"]
    )

    technician_id = created.json()["id"]

    response = client.get(
        f"/api/v1/technicians/{technician_id}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == technician_id


def test_admin_can_update_technician(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_technician(
        client,
        admin["headers"]
    )

    technician_id = created.json()["id"]

    response = client.put(
        f"/api/v1/technicians/{technician_id}",
        headers=admin["headers"],
        json={
            "specialization": "Electrical Diagnostics",
            "is_available": False
        }
    )

    assert response.status_code == 200
    assert response.json()["specialization"] == "Electrical Diagnostics"
    assert response.json()["is_available"] is False


def test_reception_cannot_update_technician(client, db):
    admin = create_test_staff(db, "ADMIN")
    reception = create_test_staff(db, "RECEPTION")

    created = create_test_technician(
        client,
        admin["headers"]
    )

    response = client.put(
        f"/api/v1/technicians/{created.json()['id']}",
        headers=reception["headers"],
        json={
            "is_available": False
        }
    )

    assert response.status_code == 403


def test_technician_not_found(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/technicians/999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404
