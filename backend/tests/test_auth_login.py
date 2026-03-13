"""
Tests for auth login OTP requirements.
"""

from datetime import datetime, timezone
import uuid

import pyotp

from app.models import Role, User, UserRole
from app.utils import hash_password


LOGIN_PATH = "/api/v1/auth/login"


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


def _create_user(
    db,
    *,
    username: str,
    email: str,
    password: str,
    role_name: str,
    otp_enabled: bool,
    otp_secret: str | None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=hash_password(password),
        first_name="Test",
        last_name="User",
        current_language="en",
        otp_enabled=otp_enabled,
        otp_secret=otp_secret,
        created_on=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        db.add(UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id))
        db.commit()

    return user


def test_login_requires_otp_for_admin_role_even_when_otp_disabled(client, db):
    _create_role(db, "admin")
    _create_user(
        db,
        username="admin_no_otp",
        email="admin_no_otp@example.com",
        password="ValidPass123!",
        role_name="admin",
        otp_enabled=False,
        otp_secret=None,
    )

    response = client.post(
        LOGIN_PATH,
        json={
            "username": "admin_no_otp",
            "password": "ValidPass123!",
        },
        headers={"Host": "localhost"},
    )

    assert response.status_code == 401


def test_login_requires_otp_for_support_role(client, db):
    _create_role(db, "support")
    secret = pyotp.random_base32()
    _create_user(
        db,
        username="support_user",
        email="support_user@example.com",
        password="ValidPass123!",
        role_name="support",
        otp_enabled=True,
        otp_secret=secret,
    )

    response = client.post(
        LOGIN_PATH,
        json={
            "username": "support_user",
            "password": "ValidPass123!",
        },
        headers={"Host": "localhost"},
    )

    assert response.status_code == 401


def test_login_for_admin_with_valid_otp_succeeds(client, db):
    _create_role(db, "admin")
    secret = pyotp.random_base32()
    _create_user(
        db,
        username="admin_otp",
        email="admin_otp@example.com",
        password="ValidPass123!",
        role_name="admin",
        otp_enabled=True,
        otp_secret=secret,
    )

    otp_code = pyotp.TOTP(secret).now()
    response = client.post(
        LOGIN_PATH,
        json={
            "username": "admin_otp",
            "password": "ValidPass123!",
            "otp_code": otp_code,
        },
        headers={"Host": "localhost"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["user"]["username"] == "admin_otp"


def test_login_for_regular_user_without_otp_still_succeeds(client, db):
    _create_role(db, "user")
    _create_user(
        db,
        username="regular_user",
        email="regular_user@example.com",
        password="ValidPass123!",
        role_name="user",
        otp_enabled=False,
        otp_secret=None,
    )

    response = client.post(
        LOGIN_PATH,
        json={
            "username": "regular_user",
            "password": "ValidPass123!",
        },
        headers={"Host": "localhost"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["username"] == "regular_user"
