from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_current_business, get_current_user
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.models import Business, Customer, User
from app.models.models import Base


@pytest.fixture
def http_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    first = Business(name="HTTP First", industry="Dental Clinic")
    second = Business(name="HTTP Second", industry="Dental Clinic")
    db.add_all([first, second])
    db.flush()
    owner = User(
        business_id=first.id,
        email="http-owner@example.com",
        name="HTTP Owner",
        hashed_password="not-used",
        role="owner",
    )
    admin = User(
        business_id=first.id,
        email="http-admin@example.com",
        name="HTTP Admin",
        hashed_password="not-used",
        role="admin",
    )
    staff = User(
        business_id=first.id,
        email="http-staff@example.com",
        name="HTTP Staff",
        hashed_password="not-used",
        role="staff",
    )
    db.add_all([owner, admin, staff])
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_business] = lambda: first
    app.dependency_overrides[get_current_user] = lambda: owner
    client = TestClient(app)
    yield client, db, first, second, owner, admin, staff
    app.dependency_overrides.clear()
    db.close()


def test_team_invitation_acceptance_is_http_scoped(http_context):
    client, db, first, second, owner, admin, staff = http_context
    response = client.post("/api/v1/team/invitations", json={"email": "new@example.com", "role": "staff"})
    assert response.status_code == 201
    token = response.json()["invitation_token"]

    accepted = client.post(
        "/api/v1/team/invitations/accept",
        json={"token": token, "name": "New Member", "password": "password123"},
    )
    assert accepted.status_code == 200
    assert db.query(User).filter(User.email == "new@example.com", User.business_id == first.id).one().role == "staff"


def test_team_role_change_removal_and_owner_transfer_are_http_scoped(http_context):
    client, db, first, second, owner, admin, staff = http_context
    changed = client.patch(f"/api/v1/team/members/{staff.id}/role", json={"role": "admin"})
    assert changed.status_code == 200
    assert changed.json()["role"] == "admin"

    transferred = client.post("/api/v1/team/transfer-ownership", json={"target_user_id": admin.id})
    assert transferred.status_code == 200
    db.refresh(owner)
    db.refresh(admin)
    assert owner.role == "admin"
    assert admin.role == "owner"

    app.dependency_overrides[get_current_user] = lambda: admin
    removed = client.delete(f"/api/v1/team/members/{staff.id}")
    assert removed.status_code == 204
    assert db.query(User).filter(User.id == staff.id).first() is None


def test_team_http_routes_reject_cross_tenant_member_ids(http_context):
    client, db, first, second, owner, admin, staff = http_context
    other = User(
        business_id=second.id,
        email="other@example.com",
        name="Other",
        hashed_password="not-used",
        role="staff",
    )
    db.add(other)
    db.commit()

    assert client.patch(f"/api/v1/team/members/{other.id}/role", json={"role": "admin"}).status_code == 404
    assert client.delete(f"/api/v1/team/members/{other.id}").status_code == 404


def test_customer_logout_revokes_token_through_http(http_context):
    client, db, first, second, owner, admin, staff = http_context
    customer = Customer(business_id=first.id, google_id="google-http", email="customer@example.com", name="Customer")
    db.add(customer)
    db.commit()
    token = create_access_token(
        data={"customer_id": str(customer.id), "business_id": first.id, "session_version": customer.session_version},
        expires_delta=timedelta(minutes=10),
    )
    client.cookies.set("followly_customer_token", token)
    logout = client.post("/api/v1/customer/auth/logout", follow_redirects=False)
    assert logout.status_code == 303
    db.refresh(customer)
    assert customer.session_version == 1
