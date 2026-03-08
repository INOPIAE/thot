"""
Tests for role management routes (admin only)
"""

import uuid

from app.models import Role, User, UserRole
from app.utils import create_access_token, hash_password


def _create_user_with_role(db, username: str, email: str, role_name: str) -> User:
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
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_list_roles_admin_allowed(client, db):
    admin_user = _create_user_with_role(db, "adminuser", "admin@example.com", "admin")

    response = client.get("/api/v1/roles", headers=_auth_headers_for_user(admin_user))

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(role["name"] == "admin" for role in data)


def test_list_roles_support_forbidden(client, db):
    _create_user_with_role(db, "adminuser", "admin@example.com", "admin")
    support_user = _create_user_with_role(db, "supportuser", "support@example.com", "support")

    response = client.get("/api/v1/roles", headers=_auth_headers_for_user(support_user))

    assert response.status_code == 403
    assert "Admin role required" in response.json()["detail"]


def test_role_crud_admin_only(client, db):
    admin_user = _create_user_with_role(db, "adminuser", "admin@example.com", "admin")
    headers = _auth_headers_for_user(admin_user)

    create_response = client.post(
        "/api/v1/roles",
        headers=headers,
        json={"name": "auditor", "description": "Read-only audit role"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "auditor"
    role_id = created["id"]

    update_response = client.put(
        f"/api/v1/roles/{role_id}",
        headers=headers,
        json={"description": "Updated description", "active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "Updated description"

    delete_response = client.delete(f"/api/v1/roles/{role_id}", headers=headers)
    assert delete_response.status_code == 204

    role = db.query(Role).filter(Role.id == uuid.UUID(role_id)).first()
    assert role is not None
    assert role.active is False


def test_system_roles_cannot_be_deleted(client, db):
    admin_user = _create_user_with_role(db, "adminuser", "admin@example.com", "admin")
    headers = _auth_headers_for_user(admin_user)

    support_role = db.query(Role).filter(Role.name == "support").first()
    if support_role is None:
        support_role = Role(name="support", description="Support role")
        db.add(support_role)
        db.commit()
        db.refresh(support_role)

    response = client.delete(f"/api/v1/roles/{support_role.id}", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete system roles"
