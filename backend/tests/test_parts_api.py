
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import Role, User, Part
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


def create_test_part(client, headers, quantity=20):
    return client.post(
        "/api/v1/parts/",
        headers=headers,
        json={
            "part_number": f"PART-{uuid.uuid4().hex[:8].upper()}",
            "name": "Engine Oil Filter",
            "description": "Replacement engine oil filter",
            "quantity_in_stock": quantity,
            "reorder_level": 5,
            "unit_cost": "120.00",
            "selling_price": "180.00"
        }
    )


def test_admin_can_create_part(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = create_test_part(
        client,
        admin["headers"]
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Engine Oil Filter"
    assert response.json()["quantity_in_stock"] == 20


def test_duplicate_part_number_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    part_number = f"PART-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "part_number": part_number,
        "name": "Brake Pad",
        "quantity_in_stock": 10,
        "reorder_level": 3,
        "unit_cost": "200.00",
        "selling_price": "300.00"
    }

    first = client.post(
        "/api/v1/parts/",
        headers=admin["headers"],
        json=payload
    )

    second = client.post(
        "/api/v1/parts/",
        headers=admin["headers"],
        json=payload
    )

    assert first.status_code == 201
    assert second.status_code == 400


@pytest.mark.parametrize(
    "role_name",
    ["ADMIN", "RECEPTION", "TECHNICIAN", "OWNER"]
)
def test_authorized_roles_can_list_parts(client, db, role_name):
    staff = create_test_staff(db, role_name)
    admin = create_test_staff(db, "ADMIN")

    create_test_part(client, admin["headers"])

    response = client.get(
        "/api/v1/parts/",
        headers=staff["headers"]
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_customer_cannot_list_parts(client, db):
    customer = create_test_staff(db, "CUSTOMER")

    response = client.get(
        "/api/v1/parts/",
        headers=customer["headers"]
    )

    assert response.status_code == 403


def test_admin_can_update_part(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_part(client, admin["headers"])
    part_id = created.json()["id"]

    response = client.put(
        f"/api/v1/parts/{part_id}",
        headers=admin["headers"],
        json={"selling_price": "220.00"}
    )

    assert response.status_code == 200
    assert float(response.json()["selling_price"]) == 220.00


def test_reception_cannot_create_part(client, db):
    reception = create_test_staff(db, "RECEPTION")

    response = create_test_part(
        client,
        reception["headers"]
    )

    assert response.status_code == 403


def test_stock_in_increases_quantity(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_part(
        client,
        admin["headers"],
        quantity=10
    )

    part_id = created.json()["id"]

    response = client.post(
        f"/api/v1/parts/{part_id}/stock-in",
        headers=admin["headers"],
        json={
            "quantity": 5,
            "reference": "PO-1001",
            "notes": "New stock received"
        }
    )

    assert response.status_code == 200
    assert response.json()["quantity_in_stock"] == 15


def test_stock_out_decreases_quantity(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_part(
        client,
        admin["headers"],
        quantity=10
    )

    part_id = created.json()["id"]

    response = client.post(
        f"/api/v1/parts/{part_id}/stock-out",
        headers=admin["headers"],
        json={"quantity": 3}
    )

    assert response.status_code == 200
    assert response.json()["quantity_in_stock"] == 7


def test_stock_out_rejects_insufficient_quantity(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_part(
        client,
        admin["headers"],
        quantity=2
    )

    response = client.post(
        f"/api/v1/parts/{created.json()['id']}/stock-out",
        headers=admin["headers"],
        json={"quantity": 5}
    )

    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_low_stock_endpoint(client, db):
    admin = create_test_staff(db, "ADMIN")

    create_test_part(
        client,
        admin["headers"],
        quantity=2
    )

    response = client.get(
        "/api/v1/parts/low-stock",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_part_transactions_are_recorded(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_part(
        client,
        admin["headers"],
        quantity=10
    )

    part_id = created.json()["id"]

    client.post(
        f"/api/v1/parts/{part_id}/stock-in",
        headers=admin["headers"],
        json={"quantity": 5}
    )

    response = client.get(
        f"/api/v1/parts/{part_id}/transactions",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["transaction_type"] == "STOCK_IN"


def test_part_not_found(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/parts/999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404
