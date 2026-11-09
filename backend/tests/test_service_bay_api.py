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
        "user": user,
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }


def create_test_bay(client, headers):
    return client.post(
        "/api/v1/service-bays/",
        headers=headers,
        json={
            "bay_number": f"BAY-{uuid.uuid4().hex[:8].upper()}",
            "description": "General vehicle servicing bay"
        }
    )


def test_admin_can_create_service_bay(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = create_test_bay(
        client,
        admin["headers"]
    )

    assert response.status_code == 201
    assert response.json()["bay_number"].startswith("BAY-")
    assert response.json()["is_active"] is True


def test_duplicate_bay_number_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    bay_number = f"BAY-{uuid.uuid4().hex[:8].upper()}"

    first_response = client.post(
        "/api/v1/service-bays/",
        headers=admin["headers"],
        json={"bay_number": bay_number}
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/service-bays/",
        headers=admin["headers"],
        json={"bay_number": bay_number}
    )

    assert second_response.status_code == 400
    assert "Bay number is already registered" in (
        second_response.json()["detail"]
    )


@pytest.mark.parametrize(
    "role_name",
    ["ADMIN", "RECEPTION", "OWNER"]
)
def test_authorized_roles_can_list_service_bays(
    client,
    db,
    role_name
):
    staff = create_test_staff(db, role_name)

    create_test_bay(
        client,
        create_test_staff(db, "ADMIN")["headers"]
    )

    response = client.get(
        "/api/v1/service-bays/",
        headers=staff["headers"]
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_customer_cannot_list_service_bays(client, db):
    customer = create_test_staff(db, "CUSTOMER")

    response = client.get(
        "/api/v1/service-bays/",
        headers=customer["headers"]
    )

    assert response.status_code == 403


def test_get_service_bay(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_bay(
        client,
        admin["headers"]
    )

    bay_id = created.json()["id"]

    response = client.get(
        f"/api/v1/service-bays/{bay_id}",
        headers=admin["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == bay_id


def test_admin_can_update_service_bay(client, db):
    admin = create_test_staff(db, "ADMIN")

    created = create_test_bay(
        client,
        admin["headers"]
    )

    bay_id = created.json()["id"]

    response = client.put(
        f"/api/v1/service-bays/{bay_id}",
        headers=admin["headers"],
        json={
            "description": "Specialised diagnostic bay",
            "is_active": False
        }
    )

    assert response.status_code == 200
    assert response.json()["description"] == (
        "Specialised diagnostic bay"
    )
    assert response.json()["is_active"] is False


def test_reception_cannot_update_service_bay(client, db):
    admin = create_test_staff(db, "ADMIN")
    reception = create_test_staff(db, "RECEPTION")

    created = create_test_bay(
        client,
        admin["headers"]
    )

    response = client.put(
        f"/api/v1/service-bays/{created.json()['id']}",
        headers=reception["headers"],
        json={"is_active": False}
    )

    assert response.status_code == 403


def test_service_bay_not_found(client, db):
    admin = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/service-bays/999999",
        headers=admin["headers"]
    )

    assert response.status_code == 404


def test_duplicate_bay_number_update_is_rejected(client, db):
    admin = create_test_staff(db, "ADMIN")

    first = create_test_bay(client, admin["headers"])
    second = create_test_bay(client, admin["headers"])

    response = client.put(
        f"/api/v1/service-bays/{second.json()['id']}",
        headers=admin["headers"],
        json={
            "bay_number": first.json()["bay_number"]
        }
    )

    assert response.status_code == 400
    assert "Bay number is already registered" in (
        response.json()["detail"]
    )