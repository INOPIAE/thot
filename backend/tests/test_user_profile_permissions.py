"""
Tests for corporate number edit permissions.
"""

from app.models import Role, User, UserRole
from app.utils import create_access_token, hash_password


def _create_user_with_role(db, username: str, email: str, role_name: str, corporate_number: str | None = None) -> User:
    """Create a user and assign the requested active role."""
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name, description=f"{role_name} role")
        db.add(role)
        db.flush()

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password("TestPassword123!"),
        active=True,
        corporate_number=corporate_number,
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id, active=True))
    db.commit()
    db.refresh(user)
    return user


def _auth_headers_for_user(user: User) -> dict:
    """Create auth headers for API calls in tests."""
    token = create_access_token(str(user.id))
    return {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
    }


def test_user_can_delete_own_account(client, db):
    """
    EN: User can delete (deactivate) their own account (soft delete)
    DE: Benutzer kann seinen eigenen Account löschen (deaktivieren, Soft-Delete)
    """
    user = _create_user_with_role(db, "deleteuser", "deleteuser@example.com", "user")
    db.refresh(user)
    print(f"[DEBUG] user.id: {user.id} (type: {type(user.id)})")
    headers = _auth_headers_for_user(user)
    print(f"[DEBUG] headers: {headers}")

    # Delete own account
    response = client.delete("/api/v1/users/delete-account", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"].startswith("Account deleted")
    # Check user is inactive in DB
    db.refresh(user)
    assert user.active is False

    # Try deleting again (should fail)
    response2 = client.delete("/api/v1/users/delete-account", headers=headers)
    assert response2.status_code == 400
    assert "already deleted" in response2.json()["detail"]


def test_user_cannot_change_own_corporate_number_via_profile(client, db):
    """Regular profile updates must not allow changing corporate_number."""
    user = _create_user_with_role(
        db,
        username="profileuser",
        email="profileuser@example.com",
        role_name="user",
        corporate_number="CORP-OLD",
    )

    response = client.put(
        "/api/v1/users/profile",
        headers=_auth_headers_for_user(user),
        json={
            "first_name": "Updated",
            "last_name": "User",
            "current_language": "de",
            "corporate_number": "CORP-NEW",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["current_language"] == "de"
    assert data["corporate_number"] == "CORP-OLD"

    db.refresh(user)
    assert user.corporate_number == "CORP-OLD"


def test_support_can_change_corporate_number(client, db):
    """Support users can change corporate_number for other users."""
    support_user = _create_user_with_role(
        db,
        username="supportuser",
        email="supportuser@example.com",
        role_name="support",
    )
    target_user = _create_user_with_role(
        db,
        username="targetuser",
        email="targetuser@example.com",
        role_name="user",
        corporate_number="CORP-001",
    )

    response = client.put(
        f"/api/v1/users/{target_user.id}",
        headers=_auth_headers_for_user(support_user),
        json={"corporate_number": "CORP-999"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["corporate_number"] == "CORP-999"

    db.refresh(target_user)
    assert target_user.corporate_number == "CORP-999"


def test_regular_user_cannot_update_other_user_via_support_endpoint(client, db):
    """Regular users must receive 403 when updating other users."""
    regular_user = _create_user_with_role(
        db,
        username="regularuser",
        email="regularuser@example.com",
        role_name="user",
    )
    target_user = _create_user_with_role(
        db,
        username="forbiddentarget",
        email="forbiddentarget@example.com",
        role_name="user",
        corporate_number="CORP-LOCKED",
    )

    response = client.put(
        f"/api/v1/users/{target_user.id}",
        headers=_auth_headers_for_user(regular_user),
        json={"corporate_number": "CORP-HACK"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"

    db.refresh(target_user)
    assert target_user.corporate_number == "CORP-LOCKED"
