import pytest
from app.models import User, UserEmailReset
from uuid import uuid4
from datetime import datetime, timezone
from app.routes import users

@pytest.fixture
def support_user(db):
    import uuid
    db.query(User).filter_by(username="supportuser").delete()
    db.commit()
    # Lege Support-Rolle an (falls nicht vorhanden)
    from app.models.role import Role
    from app.models.user_role import UserRole
    support_role = db.query(Role).filter_by(name="support").first()
    if not support_role:
        support_role = Role(id=uuid.uuid4(), name="support", description="Support role", active=True)
        db.add(support_role)
        db.commit()
        db.refresh(support_role)
    user = User(
        id=uuid.uuid4(),
        username="supportuser",
        email="support@example.com",
        hashed_password="$2b$12$1234567890123456789012abcdefghijklmno12345678901234567890",
        current_language="de",
        active=True,
        created_by=None,
        created_on=datetime.now(timezone.utc),
        last_modified_by=None,
        last_modified_on=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_role = UserRole(user_id=user.id, role_id=support_role.id, active=True)
    db.add(user_role)
    db.commit()
    yield user
    db.delete(user)
    db.commit()

def get_auth_header(user):
    return {"Authorization": f"Bearer testtoken-{user.id}"}

def test_support_email_change(monkeypatch, db, client, support_user, test_user):
    # Patch decode_access_token to always return the support user's ID
    monkeypatch.setattr("app.routes.users.decode_access_token", lambda token: str(support_user.id))

    # Patch get_current_user to return support_user for this test
    async def override_get_current_user():
        return support_user
    from app.database import get_db as real_get_db
    app = client.app
    app.dependency_overrides[users.get_current_user] = override_get_current_user
    app.dependency_overrides[real_get_db] = lambda: (yield db)

    # Patch email sending to avoid real SMTP
    from app.utils.email_service import email_service
    monkeypatch.setattr(email_service, "send_email_reset_confirmation", lambda *a, **kw: True)
    monkeypatch.setattr(email_service, "send_email_reset_info", lambda *a, **kw: True)

    # Step 1: Support requests email change for test_user
    headers = get_auth_header(support_user)
    headers["Host"] = "localhost"
    response = client.post(
        f"/api/v1/users/email-change/request/support?user_id={test_user.id}",
        json={"email": "new2@example.com"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new2@example.com"
    # Token should be in DB
    email_reset = db.query(UserEmailReset).filter_by(user_id=test_user.id).first()
    assert email_reset is not None
    token = email_reset.token
    # Token expiry should be ca. 24h (config)
    expires_at = email_reset.expires_at
    if expires_at.tzinfo is None:
        from datetime import timezone
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert (expires_at - datetime.now(timezone.utc)).total_seconds() > 23*3600

    # Step 2: Confirm email change
    response2 = client.post(
        "/api/v1/users/email-change/confirm",
        json={"token": token},
        headers={"Host": "localhost"},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["email"] == "new2@example.com"
    db.refresh(test_user)
    assert test_user.email == "new2@example.com"
    # Token removed
    assert db.query(UserEmailReset).filter_by(user_id=test_user.id).first() is None
    app.dependency_overrides = {}
