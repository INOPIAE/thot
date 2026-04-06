
import pytest
from app.models import User, UserEmailReset
from uuid import uuid4
from datetime import datetime, timezone
from app.routes import users


def get_auth_header(user):
    return {"Authorization": f"Bearer testtoken-{user.id}"}


def test_email_change_request_and_confirm(monkeypatch, db, client, test_user):
    # Patch decode_access_token to always return the test user's ID
    monkeypatch.setattr("app.routes.users.decode_access_token", lambda token: str(test_user.id))

    # Patch get_current_user to return test_user for this test
    async def override_get_current_user():
        return test_user
    from app.database import get_db as real_get_db
    app = client.app
    app.dependency_overrides[users.get_current_user] = override_get_current_user
    app.dependency_overrides[real_get_db] = lambda: (yield db)

    # Patch email sending to avoid real SMTP
    from app.utils.email_service import email_service
    monkeypatch.setattr(email_service, "send_email_reset_confirmation", lambda *a, **kw: True)
    monkeypatch.setattr(email_service, "send_email_reset_info", lambda *a, **kw: True)

    # Step 1: Request email change
    headers = get_auth_header(test_user)
    headers["Host"] = "localhost"
    response = client.post(
        "/api/v1/users/email-change/request",
        json={"email": "new@example.com"},
        headers=headers,
    )
    if response.status_code != 200:
        print("DEBUG response:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    # Token should be in DB
    email_reset = db.query(UserEmailReset).filter_by(user_id=test_user.id).first()
    assert email_reset is not None
    token = email_reset.token

    # Step 2: Confirm email change
    response2 = client.post(
        "/api/v1/users/email-change/confirm",
        json={"token": token},
        headers={"Host": "localhost"},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["email"] == "new@example.com"
    # User email updated
    db.refresh(test_user)
    assert test_user.email == "new@example.com"
    # Token removed
    assert db.query(UserEmailReset).filter_by(user_id=test_user.id).first() is None

    # Clean up dependency overrides
    app.dependency_overrides = {}
