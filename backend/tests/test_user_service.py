"""
Tests for User Service
"""

import pytest
from datetime import datetime, timezone
from app.services import UserService
from app.models import User, Role, UserRole
from app.utils import verify_password, hash_password
import uuid


@pytest.fixture
def setup_roles(db):
    """Setup default roles"""
    admin_role = Role(
        id=uuid.uuid4(),
        name="admin",
        description="Admin role",
        active=True,
        created_on=datetime.now(timezone.utc)
    )
    user_role = Role(
        id=uuid.uuid4(),
        name="user",
        description="User role",
        active=True,
        created_on=datetime.now(timezone.utc)
    )
    db.add(admin_role)
    db.add(user_role)
    db.commit()
    return {"admin": admin_role, "user": user_role}


def test_create_user(db, setup_roles):
    """Test creating a new user"""
    user = UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User",
        is_first_user=False
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert verify_password("TestPassword123!", user.hashed_password)


def test_create_first_user_as_admin(db, setup_roles):
    """Test that first user gets admin role"""
    user = UserService.create_user(
        db=db,
        username="admin",
        email="admin@example.com",
        password="AdminPassword123!",
        is_first_user=True
    )

    assert len(user.user_roles) > 0
    assert any(ur.role.name == "admin" for ur in user.user_roles)


def test_get_user_by_username(db, setup_roles):
    """Test getting user by username"""
    UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        is_first_user=False
    )

    user = UserService.get_user_by_username(db, "testuser")
    assert user is not None
    assert user.username == "testuser"


def test_get_user_by_email(db, setup_roles):
    """Test getting user by email"""
    UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        is_first_user=False
    )

    user = UserService.get_user_by_email(db, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"


def test_authenticate_user_success(db, setup_roles):
    """Test successful user authentication"""
    UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        is_first_user=False
    )

    user, error = UserService.authenticate_user(
        db=db,
        username="testuser",
        password="TestPassword123!"
    )

    assert user is not None
    assert user.username == "testuser"
    assert error == ""
    assert user.unsuccessful_logins == 0


def test_authenticate_user_invalid_password(db, setup_roles):
    """Test authentication with invalid password"""
    UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        is_first_user=False
    )

    user, error = UserService.authenticate_user(
        db=db,
        username="testuser",
        password="WrongPassword123!"
    )

    assert user is None
    assert error != ""

    # Check that unsuccessful logins counter increased
    user_from_db = UserService.get_user_by_username(db, "testuser")
    assert user_from_db.unsuccessful_logins == 1


def test_update_user_profile(db, setup_roles):
    """Test updating user profile"""
    user = UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User",
        is_first_user=False
    )

    updated_user = UserService.update_user_profile(
        db=db,
        user_id=str(user.id),
        first_name="Updated",
        last_name="Name",
        current_language="de"
    )

    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.current_language == "de"


def test_change_password(db, setup_roles):
    """Test changing password"""
    user = UserService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="OldPassword123!",
        is_first_user=False
    )

    success, message = UserService.change_password(
        db=db,
        user_id=str(user.id),
        current_password="OldPassword123!",
        new_password="NewPassword456!"
    )

    assert success is True
    
    # Verify new password works
    user_updated, error = UserService.authenticate_user(
        db=db,
        username="testuser",
        password="NewPassword456!"
    )
    assert user_updated is not None


def test_inactive_user_role_not_effective(db, setup_roles):
    """Inactive user_roles must not grant role checks or role listing"""
    user = UserService.create_user(
        db=db,
        username="rolecheck",
        email="rolecheck@example.com",
        password="TestPassword123!",
        is_first_user=False,
    )

    admin_role = setup_roles["admin"]
    assignment = UserRole(
        id=uuid.uuid4(),
        user_id=user.id,
        role_id=admin_role.id,
        active=False,
        created_on=datetime.now(timezone.utc),
    )
    db.add(assignment)
    db.commit()
    db.refresh(user)

    assert user.has_role("admin") is False
    assert "admin" not in user.get_roles()


def test_removed_role_cannot_be_reassigned(db, setup_roles):
    """Soft-deleted role assignments cannot be reactivated via new assignment"""
    user = UserService.create_user(
        db=db,
        username="softdelete",
        email="softdelete@example.com",
        password="TestPassword123!",
        is_first_user=False,
    )
    admin_role = setup_roles["admin"]
    actor_id = str(user.id)

    assigned, err = UserService.assign_role_to_user(
        db=db,
        user_id=str(user.id),
        role_id=str(admin_role.id),
        assigned_by=actor_id,
    )
    assert assigned is not None
    assert err is None

    removed, err = UserService.remove_role_from_user(
        db=db,
        user_id=str(user.id),
        role_id=str(admin_role.id),
        removed_by=actor_id,
    )
    assert removed is True
    assert err is None

    reassigned, err = UserService.assign_role_to_user(
        db=db,
        user_id=str(user.id),
        role_id=str(admin_role.id),
        assigned_by=actor_id,
    )
    assert reassigned is None
    assert err == "Role assignment was previously removed and cannot be reactivated"
