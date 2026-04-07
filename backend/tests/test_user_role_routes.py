"""
Tests for user role assignment routes (support/admin)
"""

import uuid

from app.models import Role, User, UserRole
from app.utils import create_access_token, hash_password


def _create_user_with_role(db, username: str, email: str, role_name: str) -> User:
    """Helper to create user with specific role"""
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

    db.add(UserRole(user_id=user.id, role_id=role.id, active=True))
    db.commit()
    db.refresh(user)
    return user


def _auth_headers_for_user(user: User) -> dict:
    """Helper to create auth headers for user"""
    token = create_access_token(str(user.id))
    return {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
    }


def test_support_can_get_user_roles(client, db):
    """Support users can get role list for a user"""
    support_user = _create_user_with_role(db, "supportuser", "support@example.com", "support")
    target_user = _create_user_with_role(db, "targetuser", "target@example.com", "user")

    response = client.get(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(support_user),
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(r["role_name"] == "user" for r in data)


def test_support_can_assign_role_to_user(client, db):
    """Support users can assign roles to users"""
    support_user = _create_user_with_role(db, "supportuser", "support@example.com", "support")
    target_user = _create_user_with_role(db, "targetuser", "target@example.com", "user")
    
    # Create additional role
    scan_role = Role(name="user_scan", description="Scan role")
    db.add(scan_role)
    db.commit()
    db.refresh(scan_role)

    response = client.post(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(support_user),
        json={"role_id": str(scan_role.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role_name"] == "user_scan"
    assert data["active"] is True


def test_support_can_remove_role_from_user(client, db):
    """Support users can remove (soft-delete) roles from users"""
    support_user = _create_user_with_role(db, "supportuser", "support@example.com", "support")
    target_user = _create_user_with_role(db, "targetuser", "target@example.com", "user")
    
    user_role_obj = db.query(Role).filter(Role.name == "user").first()

    response = client.delete(
        f"/api/v1/users/{target_user.id}/roles/{user_role_obj.id}",
        headers=_auth_headers_for_user(support_user),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Role removed successfully"

    # Verify role is soft-deleted
    assignment = db.query(UserRole).filter(
        UserRole.user_id == target_user.id,
        UserRole.role_id == user_role_obj.id,
    ).first()
    assert assignment is not None
    assert assignment.active is False


def test_cannot_reassign_removed_role(client, db):
    """Once a role is removed, it cannot be reassigned to the same user"""
    admin_user = _create_user_with_role(db, "adminuser", "admin@example.com", "admin")
    target_user = _create_user_with_role(db, "targetuser", "target@example.com", "user")
    
    # Create scan role
    scan_role = Role(name="user_scan", description="Scan role")
    db.add(scan_role)
    db.commit()
    db.refresh(scan_role)

    # Assign role
    assign_response = client.post(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(admin_user),
        json={"role_id": str(scan_role.id)},
    )
    assert assign_response.status_code == 201

    # Remove role
    remove_response = client.delete(
        f"/api/v1/users/{target_user.id}/roles/{scan_role.id}",
        headers=_auth_headers_for_user(admin_user),
    )
    assert remove_response.status_code == 200

    # Try to reassign - should fail
    reassign_response = client.post(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(admin_user),
        json={"role_id": str(scan_role.id)},
    )
    assert reassign_response.status_code == 400
    assert "previously removed" in reassign_response.json()["detail"].lower()


def test_regular_user_cannot_assign_roles(client, db):
    """Regular users cannot assign roles"""
    regular_user = _create_user_with_role(db, "regularuser", "regular@example.com", "user")
    target_user = _create_user_with_role(db, "targetuser", "target@example.com", "user")
    
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Admin role")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    response = client.post(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(regular_user),
        json={"role_id": str(admin_role.id)},
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]

def test_assign_support_role_requires_otp(client, db):
    """Assigning support/admin role to user without OTP enabled returns 400"""
    admin_user = _create_user_with_role(db, "adminuser2", "admin2@example.com", "admin")
    target_user = _create_user_with_role(db, "targetuser2", "target2@example.com", "user")
    support_role = db.query(Role).filter(Role.name == "support").first()
    if not support_role:
        support_role = Role(name="support", description="Support role")
        db.add(support_role)
        db.commit()
        db.refresh(support_role)

    assign_response = client.post(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(admin_user),
        json={"role_id": str(support_role.id)},
    )
    assert assign_response.status_code == 400
    assert "otp required" in assign_response.json()["detail"].lower()

def test_assign_support_role_with_otp_success(client, db):
    """Assigning support/admin role to user WITH OTP enabled returns 201"""
    admin_user = _create_user_with_role(db, "adminuser3", "admin3@example.com", "admin")
    target_user = _create_user_with_role(db, "targetuser3", "target3@example.com", "user")
    # Enable OTP for target user
    target_user.otp_enabled = True
    db.commit()
    support_role = db.query(Role).filter(Role.name == "support").first()
    if not support_role:
        support_role = Role(name="support", description="Support role")
        db.add(support_role)
        db.commit()
        db.refresh(support_role)

    assign_response = client.post(
        f"/api/v1/users/{target_user.id}/roles",
        headers=_auth_headers_for_user(admin_user),
        json={"role_id": str(support_role.id)},
    )
    assert assign_response.status_code == 201
