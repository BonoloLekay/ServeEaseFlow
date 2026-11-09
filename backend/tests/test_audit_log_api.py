
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models import AuditLog, Role, User
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
        first_name="Audit",
        last_name="Tester"
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


def create_test_audit_log(db, user_id=None):
    audit_log = AuditLog(
        user_id=user_id,
        action="CREATE",
        entity_type="Vehicle",
        entity_id=str(uuid.uuid4()),
        description="Test audit log entry",
        old_values=None,
        new_values={"make": "BMW", "model": "320i"},
        ip_address="127.0.0.1"
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def test_admin_can_view_audit_logs(client, db):
    staff = create_test_staff(db, "ADMIN")
    create_test_audit_log(db, staff["user"].id)

    response = client.get(
        "/api/v1/audit-logs/",
        headers=staff["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["action"] == "CREATE"


def test_owner_can_view_audit_logs(client, db):
    staff = create_test_staff(db, "OWNER")
    create_test_audit_log(db, staff["user"].id)

    response = client.get(
        "/api/v1/audit-logs/",
        headers=staff["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.parametrize("role_name", [
    "RECEPTION",
    "TECHNICIAN"
])
def test_unauthorised_staff_cannot_view_audit_logs(
    client,
    db,
    role_name
):
    staff = create_test_staff(db, role_name)

    response = client.get(
        "/api/v1/audit-logs/",
        headers=staff["headers"]
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_audit_logs(client):
    response = client.get("/api/v1/audit-logs/")

    assert response.status_code == 401


def test_audit_logs_support_pagination(client, db):
    staff = create_test_staff(db, "ADMIN")

    for _ in range(3):
        create_test_audit_log(db, staff["user"].id)

    response = client.get(
        "/api/v1/audit-logs/?skip=0&limit=2",
        headers=staff["headers"]
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_audit_logs_reject_invalid_pagination(client, db):
    staff = create_test_staff(db, "ADMIN")

    response = client.get(
        "/api/v1/audit-logs/?skip=-1",
        headers=staff["headers"]
    )

    assert response.status_code == 422
