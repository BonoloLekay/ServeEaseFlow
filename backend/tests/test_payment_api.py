
import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import Role, User, Invoice
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
    email = f"payment_{uuid.uuid4().hex[:8]}@example.com"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Payment",
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
            "registration_number": f"PAY{uuid.uuid4().hex[:6].upper()}",
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
            "reported_issue": "Payment testing - engine inspection.",
            "odometer_reading": 45000
        }
    )

    assert response.status_code == 201
    return response.json()



def create_test_invoice(client, staff):
    job_card = create_test_job_card(client, staff)

    # Create a part with a positive selling price.
    part_response = client.post(
        "/api/v1/parts/",
        headers=staff["headers"],
        json={
            "part_number": f"PAY-{uuid.uuid4().hex[:8].upper()}",
            "name": "Payment Test Oil Filter",
            "description": "Part for payment API testing",
            "quantity_in_stock": 20,
            "reorder_level": 5,
            "unit_cost": "100.00",
            "selling_price": "220.00"
        }
    )

    assert part_response.status_code == 201
    part = part_response.json()

    # Add the part to the job card.
    usage_response = client.post(
        f"/api/v1/parts/job-cards/{job_card['id']}/usage",
        headers=staff["headers"],
        json={
            "part_id": part["id"],
            "quantity_used": 1
        }
    )

    assert usage_response.status_code == 201

    # Move job card to IN_PROGRESS.
    response = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=staff["headers"],
        json={"status": "IN_PROGRESS"}
    )

    assert response.status_code == 200

    # Complete job card.
    response = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=staff["headers"],
        json={"status": "COMPLETED"}
    )

    assert response.status_code == 200

    # Generate invoice.
    response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=staff["headers"]
    )

    assert response.status_code == 201
    return response.json()

    job_card = create_test_job_card(client, staff)

    # Move job card to IN_PROGRESS.
    response = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=staff["headers"],
        json={"status": "IN_PROGRESS"}
    )

    assert response.status_code == 200

    # Complete job card.
    response = client.patch(
        f"/api/v1/job-cards/{job_card['id']}/status",
        headers=staff["headers"],
        json={"status": "COMPLETED"}
    )

    assert response.status_code == 200

    # Generate invoice.
    response = client.post(
        f"/api/v1/invoices/?job_card_id={job_card['id']}",
        headers=staff["headers"]
    )

    assert response.status_code == 201
    return response.json()


def test_admin_can_create_pending_payment(client, db):
    admin = create_test_staff(db, "ADMIN")
    invoice = create_test_invoice(client, admin)

    response = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": invoice["id"]}
    )

    assert response.status_code == 201

    data = response.json()

    assert data["invoice_id"] == invoice["id"]
    assert data["payment_method"] == "PAYFAST"
    assert data["status"] == "PENDING"
    assert data["payment_reference"].startswith("SE-")
    assert Decimal(data["amount"]) == Decimal(invoice["total_amount"])


def test_reception_can_create_pending_payment(client, db):
    admin = create_test_staff(db, "ADMIN")
    reception = create_test_staff(db, "RECEPTION")

    invoice = create_test_invoice(client, admin)

    response = client.post(
        "/api/v1/payments/",
        headers=reception["headers"],
        json={"invoice_id": invoice["id"]}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"


def test_customer_cannot_pay_another_customers_invoice(client, db):
    admin = create_test_staff(db, "ADMIN")
    invoice = create_test_invoice(client, admin)

    customer = create_test_customer(client)

    response = client.post(
        "/api/v1/payments/",
        headers=customer["headers"],
        json={"invoice_id": invoice["id"]}
    )

    assert response.status_code == 404


def test_payment_for_nonexistent_invoice_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": 999999999}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invoice not found."


def test_duplicate_pending_payment_returns_existing_payment(client, db):
    admin = create_test_staff(db, "ADMIN")
    invoice = create_test_invoice(client, admin)

    first = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": invoice["id"]}
    )

    second = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": invoice["id"]}
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] == second.json()["id"]
    assert (
        first.json()["payment_reference"]
        == second.json()["payment_reference"]
    )



def test_admin_can_list_payments(client, db):
    admin = create_test_staff(db, "ADMIN")
    invoice = create_test_invoice(client, admin)

    payment_response = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": invoice["id"]}
    )

    assert payment_response.status_code == 201
    payment_id = payment_response.json()["id"]

    response = client.get(
        "/api/v1/payments/",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert any(
        payment["id"] == payment_id
        for payment in response.json()
    )


def test_admin_can_retrieve_payment(client, db):
    admin = create_test_staff(db, "ADMIN")
    invoice = create_test_invoice(client, admin)

    created = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": invoice["id"]}
    )

    payment_id = created.json()["id"]

    response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == payment_id


def test_admin_can_retrieve_invoice_payments(client, db):
    admin = create_test_staff(db, "ADMIN")
    invoice = create_test_invoice(client, admin)

    created = client.post(
        "/api/v1/payments/",
        headers=admin["headers"],
        json={"invoice_id": invoice["id"]}
    )

    assert created.status_code == 201

    response = client.get(
        f"/api/v1/payments/invoice/{invoice['id']}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == created.json()["id"]


def test_customer_cannot_list_all_payments(client, db):
    customer = create_test_staff(db, "CUSTOMER")

    response = client.get(
        "/api/v1/payments/",
        headers=customer["headers"]
    )

    assert response.status_code == 403


def test_reception_cannot_retrieve_nonexistent_payment(client, db):
    reception = create_test_staff(db, "RECEPTION")

    response = client.get(
        "/api/v1/payments/999999999",
        headers=reception["headers"]
    )

    assert response.status_code == 404


def test_staff_cannot_view_payments_for_nonexistent_invoice(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/payments/invoice/999999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404
