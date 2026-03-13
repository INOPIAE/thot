"""
Tests for password reset flow
"""

from datetime import datetime, timezone
import uuid

from app.models import Role, User, UserRole, PasswordResetToken
from app.utils import hash_password, create_access_token, verify_password


def _create_role(db, name: str) -> Role:
    role = Role(
        id=uuid.uuid4(),
        name=name,
        description=f"{name} role",
        active=True,
        created_on=datetime.now(timezone.utc),
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _create_user(db, username: str, email: str, password: str, role_name: str = "user") -> User:
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=hash_password(password),
        first_name="Test",
        last_name="User",
        current_language="en",
        created_on=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        user_role = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id)
        db.add(user_role)
        db.commit()

    return user


def test_password_reset_request_uses_username(client, db, monkeypatch):
    _create_role(db, "user")
    _create_user(db, "alice", "alice@example.com", "ValidPass123!", "user")

    monkeypatch.setattr(
        "app.routes.auth.email_service.send_password_reset_email",
        lambda *args, **kwargs: True,
    )

    response = client.post(
        "/api/v1/auth/password-reset",
        json={"username": "alice"},
        headers={"Host": "localhost"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "If the username exists" in data["message"]

    token = db.query(PasswordResetToken).filter(PasswordResetToken.used.is_(False)).first()
    assert token is not None
    assert token.userid is not None


def test_password_reset_confirm_flow_updates_password_and_marks_used(client, db, monkeypatch):
    _create_role(db, "user")
    user = _create_user(db, "bob", "bob@example.com", "ValidPass123!", "user")

    monkeypatch.setattr(
        "app.routes.auth.email_service.send_password_reset_email",
        lambda *args, **kwargs: True,
    )

    request_response = client.post(
        "/api/v1/auth/password-reset",
        json={"username": "bob"},
        headers={"Host": "localhost"},
    )
    assert request_response.status_code == 200

    token_entry = db.query(PasswordResetToken).filter(PasswordResetToken.userid == user.id).first()
    assert token_entry is not None

    validate_response = client.get(
        f"/api/v1/auth/password-reset/confirm/{token_entry.token}",
        headers={"Host": "localhost"},
    )
    assert validate_response.status_code == 200

    confirm_response = client.post(
        f"/api/v1/auth/password-reset/confirm/{token_entry.token}",
        json={
            "new_password": "NewValidPass456!",
            "new_password_confirm": "NewValidPass456!",
        },
        headers={"Host": "localhost"},
    )
    assert confirm_response.status_code == 200

    db.refresh(token_entry)
    assert token_entry.used is True

    db.refresh(user)
    assert verify_password("NewValidPass456!", user.hashed_password)


def test_support_can_start_password_reset_for_user(client, db, monkeypatch):
    _create_role(db, "support")
    _create_role(db, "user")

    support_user = _create_user(db, "support1", "support@example.com", "ValidPass123!", "support")
    target_user = _create_user(db, "charlie", "charlie@example.com", "ValidPass123!", "user")

    monkeypatch.setattr(
        "app.routes.users.email_service.send_password_reset_email",
        lambda *args, **kwargs: True,
    )

    access_token = create_access_token(str(support_user.id))
    response = client.put(
        f"/api/v1/users/{target_user.id}/password-reset",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["expires_in_hours"] == 24

    token_entry = db.query(PasswordResetToken).filter(PasswordResetToken.userid == target_user.id).first()
    assert token_entry is not None
