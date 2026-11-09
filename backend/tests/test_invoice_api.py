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
    email = f"invoice_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Invoice",
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
            "registration_number": f"IV{uuid.uuid4().hex[:6].upper()}",
            "vin": uuid.uuid4().hex[:17].upper(),
            "make": "BMW",
            "model": "320i",
            "year": 2023,
            "colour": "Black"
        }
    )

    assert response.status_code == 201
    return response.json()

def create_test_technician(client, admin):
    response = client.post(
        "/api/v1/technicians/",
        headers=admin["headers"],
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

def create_test_job_card(client, staff):
    customer = create_test_customer(client)
    vehicle = create_test_vehicle(client, customer)

    response = client.post(
        "/api/v1/job-cards/",
        headers=staff["headers"],
        json={
            "vehicle_id": vehicle["id"],
            "reported_issue": "Invoice testing - engine inspection.",
            "odometer_reading": 45000
        }
    )

    assert response.status_code == 201
    return response.json()

def complete_job_card(client, staff, job_card_id):
    response = client.patch(
        f"/api/v1/job-cards/{job_card_id}/status",
        headers=staff["headers"],
        json={
            "status": "IN_PROGRESS"
        }
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/job-cards/{job_card_id}/status",
        headers=staff["headers"],
        json={
            "status": "COMPLETED"
        }
    )

    assert response.status_code == 200


def test_admin_can_generate_invoice(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)

    complete_job_card(
        client,
        admin,
        job_card["id"]
    )

    response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=admin["headers"]
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_card_id"] == job_card["id"]
    assert data["status"] == "UNPAID"
    assert Decimal(data["subtotal"]) == Decimal("0.00")
    assert Decimal(data["tax_amount"]) == Decimal("0.00")
    assert Decimal(data["total_amount"]) == Decimal("0.00")
    assert data["invoice_number"].startswith("INV-")


def test_invoice_cannot_be_generated_for_incomplete_job_card(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)

    response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=admin["headers"]
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "An invoice can only be generated for a completed job card."
    )

def test_duplicate_invoice_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    job_card = create_test_job_card(client, admin)

    complete_job_card(
        client,
        admin,
        job_card["id"]
    )

    first = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=admin["headers"]
    )

    second = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=admin["headers"]
    )

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == (
        "An invoice already exists for this job card."
    )

def test_customer_cannot_generate_invoice(client, db):
    admin = create_test_staff(db, "ADMIN")
    customer = create_test_staff(db, "CUSTOMER")

    job_card = create_test_job_card(client, admin)

    complete_job_card(
        client,
        admin,
        job_card["id"]
    )

    response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=customer["headers"]
    )

    assert response.status_code == 403

def test_reception_can_generate_invoice(client, db):
    admin = create_test_staff(db, "ADMIN")
    reception = create_test_staff(db, "RECEPTION")

    job_card = create_test_job_card(client, admin)

    complete_job_card(
        client,
        admin,
        job_card["id"]
    )

    response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=reception["headers"]
    )

    assert response.status_code == 201
    assert response.json()["status"] == "UNPAID"

def test_invoice_calculates_labour_parts_and_vat(client, db):
    admin = create_test_staff(db, "ADMIN")

    # Create job card
    job_card = create_test_job_card(client, admin)
    job_card_id = job_card["id"]

    # Create technician
    technician = create_test_technician(client, admin)

    # Create part
    part_response = client.post(
        "/api/v1/parts/",
        headers=admin["headers"],
        json={
            "part_number": f"INV-{uuid.uuid4().hex[:8].upper()}",
            "name": "Engine Oil Filter",
            "description": "Invoice calculation test",
            "quantity_in_stock": 20,
            "reorder_level": 5,
            "unit_cost": "150.00",
            "selling_price": "220.00"
        }
    )

    assert part_response.status_code == 201
    part = part_response.json()

    # Add two parts to the job card
    usage_response = client.post(
        f"/api/v1/parts/job-cards/{job_card_id}/usage",
        headers=admin["headers"],
        json={
            "part_id": part["id"],
            "quantity_used": 2
        }
    )

    assert usage_response.status_code == 201

    # Record labour
    labour_response = client.post(
        "/api/v1/labour/",
        headers=admin["headers"],
        json={
            "job_card_id": job_card_id,
            "technician_id": technician["id"],
            "description": "Engine diagnostics and inspection",
            "hours_worked": "2.50",
            "hourly_rate": "650.00"
        }
    )

    assert labour_response.status_code == 201

    # Complete job card
    complete_job_card(client, admin, job_card_id)

    # Generate invoice
    invoice_response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card_id}",
        headers=admin["headers"]
    )

    assert invoice_response.status_code == 201

    invoice = invoice_response.json()

    # Verify financial calculations
    assert Decimal(invoice["subtotal"]) == Decimal("2065.00")
    assert Decimal(invoice["tax_amount"]) == Decimal("309.75")
    assert Decimal(invoice["total_amount"]) == Decimal("2374.75")
    assert invoice["status"] == "UNPAID"

def test_admin_can_list_and_retrieve_invoices(client, db):
    admin = create_test_staff(db, "ADMIN")
    job_card = create_test_job_card(client, admin)

    complete_job_card(client, admin, job_card["id"])

    create_response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=admin["headers"]
    )

    assert create_response.status_code == 201
    invoice_id = create_response.json()["id"]

    # List invoices
    list_response = client.get(
        "/api/v1/invoices/",
        headers=admin["headers"]
    )

    assert list_response.status_code == 200
    assert any(
        invoice["id"] == invoice_id
        for invoice in list_response.json()
    )

    # Retrieve by invoice ID
    detail_response = client.get(
        f"/api/v1/invoices/{invoice_id}",
        headers=admin["headers"]
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == invoice_id

    # Retrieve by job card ID
    job_card_response = client.get(
        f"/api/v1/invoices/job-cards/{job_card['id']}",
        headers=admin["headers"]
    )

    assert job_card_response.status_code == 200
    assert job_card_response.json()["id"] == invoice_id


def test_customer_cannot_list_invoices(client, db):
    customer = create_test_staff(db, "CUSTOMER")

    response = client.get(
        "/api/v1/invoices/",
        headers=customer["headers"]
    )

    assert response.status_code == 403