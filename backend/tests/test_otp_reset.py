"""
Tests for OTP reset flow
"""

from datetime import datetime, timezone
import uuid

import pyotp

from app.models import Role, User, UserRole, OTPResetToken
from app.utils import hash_password, create_access_token
from config import config


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
        otp_secret=pyotp.random_base32(),
        otp_enabled=True,
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


def test_user_can_start_otp_reset(client, db):
    _create_role(db, "user")
    user = _create_user(db, "otpuser", "otpuser@example.com", "ValidPass123!", "user")

    access_token = create_access_token(str(user.id))
    response = client.post(
        "/api/v1/users/otp/reset",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["expires_in_hours"] == 1
    assert payload["token"]
    assert payload["otp_setup"]["manual_entry"]
    assert payload["otp_setup"]["qr_code"]

    token_entry = db.query(OTPResetToken).filter(OTPResetToken.userid == user.id).first()
    assert token_entry is not None
    assert token_entry.used is False


def test_user_can_confirm_otp_reset(client, db):
    _create_role(db, "user")
    user = _create_user(db, "otpconfirm", "otpconfirm@example.com", "ValidPass123!", "user")
    previous_secret = user.otp_secret

    access_token = create_access_token(str(user.id))
    start_response = client.post(
        "/api/v1/users/otp/reset",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
    )
    assert start_response.status_code == 200

    token_entry = db.query(OTPResetToken).filter(OTPResetToken.userid == user.id).first()
    assert token_entry is not None

    otp_code = pyotp.TOTP(token_entry.otp_token).now()
    confirm_response = client.post(
        "/api/v1/users/otp/reset/confirm",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
        json={
            "token": token_entry.token,
            "otp_code": otp_code,
        },
    )

    assert confirm_response.status_code == 200

    db.refresh(token_entry)
    db.refresh(user)
    assert token_entry.used is True
    assert user.otp_enabled is True
    assert user.otp_secret == token_entry.otp_token
    assert user.otp_secret != previous_secret


def test_user_cannot_confirm_otp_reset_with_invalid_code(client, db):
    _create_role(db, "user")
    user = _create_user(db, "otpinvalid", "otpinvalid@example.com", "ValidPass123!", "user")
    previous_secret = user.otp_secret

    access_token = create_access_token(str(user.id))
    start_response = client.post(
        "/api/v1/users/otp/reset",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
    )
    assert start_response.status_code == 200

    token_entry = db.query(OTPResetToken).filter(OTPResetToken.userid == user.id).first()
    assert token_entry is not None

    confirm_response = client.post(
        "/api/v1/users/otp/reset/confirm",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
        json={
            "token": token_entry.token,
            "otp_code": "000000",
        },
    )

    assert confirm_response.status_code == 400

    db.refresh(token_entry)
    db.refresh(user)
    assert token_entry.used is False
    assert user.otp_secret == previous_secret


def test_support_can_start_otp_reset_for_user(client, db, monkeypatch):
    _create_role(db, "user")
    _create_role(db, "support")

    monkeypatch.setattr(
        "app.routes.users.email_service.send_otp_reset_email",
        lambda **kwargs: True,
    )

    target_user = _create_user(db, "otp_target", "otp-target@example.com", "ValidPass123!", "user")
    support_user = _create_user(db, "otp_support", "otp-support@example.com", "ValidPass123!", "support")

    access_token = create_access_token(str(support_user.id))
    response = client.put(
        f"/api/v1/users/{target_user.id}/otp-reset",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["expires_in_hours"] == config.SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS

    token_entry = (
        db.query(OTPResetToken)
        .filter(
            OTPResetToken.userid == target_user.id,
            OTPResetToken.used.is_(False),
        )
        .first()
    )
    assert token_entry is not None
    assert token_entry.token
    assert token_entry.otp_token


def test_regular_user_cannot_start_otp_reset_for_user(client, db):
    _create_role(db, "user")

    regular_user = _create_user(db, "otp_regular", "otp-regular@example.com", "ValidPass123!", "user")
    target_user = _create_user(db, "otp_other", "otp-other@example.com", "ValidPass123!", "user")

    access_token = create_access_token(str(regular_user.id))
    response = client.put(
        f"/api/v1/users/{target_user.id}/otp-reset",
        headers={"Authorization": f"Bearer {access_token}", "Host": "localhost"},
    )

    assert response.status_code == 403