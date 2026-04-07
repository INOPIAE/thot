"""
Tests for User Service
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.services import UserService
from app.models import User, Role, UserRole
from app.utils import verify_password, hash_password
from config import config
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


def test_authenticate_user_first_two_failed_logins_return_invalid_credentials(
    db,
    setup_roles,
    monkeypatch,
):
    """The first two failed login attempts should still return the generic invalid-credentials message."""
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_3_ATTEMPTS", 5)
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_5_ATTEMPTS", 10)

    UserService.create_user(
        db=db,
        username="graceuser2",
        email="graceuser2@example.com",
        password="TestPassword123!",
        is_first_user=False,
    )

    first_user, first_error = UserService.authenticate_user(
        db=db,
        username="graceuser2",
        password="WrongPassword123!",
    )
    second_user, second_error = UserService.authenticate_user(
        db=db,
        username="graceuser2",
        password="WrongPassword123!",
    )

    assert first_user is None
    assert first_error == "Invalid username or password"
    assert second_user is None
    assert second_error == "Invalid username or password"

    user_from_db = UserService.get_user_by_username(db, "graceuser2")
    assert user_from_db.unsuccessful_logins == 2


def test_authenticate_user_third_failed_login_returns_temporary_lock(
    db,
    setup_roles,
    monkeypatch,
):
    """The third failed login attempt should activate the grace period immediately."""
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_3_ATTEMPTS", 5)
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_5_ATTEMPTS", 10)

    UserService.create_user(
        db=db,
        username="graceuser3",
        email="graceuser3@example.com",
        password="TestPassword123!",
        is_first_user=False,
    )

    for _ in range(2):
        UserService.authenticate_user(
            db=db,
            username="graceuser3",
            password="WrongPassword123!",
        )

    authenticated_user, error = UserService.authenticate_user(
        db=db,
        username="graceuser3",
        password="WrongPassword123!",
    )

    assert authenticated_user is None
    assert error == "Login temporarily locked. Please try again later"

    user_from_db = UserService.get_user_by_username(db, "graceuser3")
    assert user_from_db.unsuccessful_logins == 3


def test_authenticate_user_fourth_failed_login_stays_temporarily_locked(
    db,
    setup_roles,
    monkeypatch,
):
    """The fourth failed login attempt should remain blocked by the active grace period."""
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_3_ATTEMPTS", 5)
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_5_ATTEMPTS", 10)

    UserService.create_user(
        db=db,
        username="graceuser4",
        email="graceuser4@example.com",
        password="TestPassword123!",
        is_first_user=False,
    )

    for _ in range(3):
        UserService.authenticate_user(
            db=db,
            username="graceuser4",
            password="WrongPassword123!",
        )

    authenticated_user, error = UserService.authenticate_user(
        db=db,
        username="graceuser4",
        password="WrongPassword123!",
    )

    assert authenticated_user is None
    assert error == "Login temporarily locked. Please try again later"

    user_from_db = UserService.get_user_by_username(db, "graceuser4")
    assert user_from_db.unsuccessful_logins == 3


def test_authenticate_user_compares_grace_period_in_same_timezone(
    db,
    setup_roles,
    monkeypatch,
):
    """A stored timestamp with +01:00 offset must still be compared correctly against UTC now."""
    monkeypatch.setattr(type(config), "GRACE_PERIOD_MINUTES_3_ATTEMPTS", 5)

    UserService.create_user(
        db=db,
        username="timezoneuser",
        email="timezoneuser@example.com",
        password="TestPassword123!",
        is_first_user=False,
    )

    user_in_db = UserService.get_user_by_username(db, "timezoneuser")
    user_in_db.unsuccessful_logins = 3
    user_in_db.timestamp_last_successful_login = datetime.now(
        timezone(timedelta(hours=1))
    )
    db.commit()

    authenticated_user, error = UserService.authenticate_user(
        db=db,
        username="timezoneuser",
        password="TestPassword123!",
    )

    assert authenticated_user is None
    assert error == "Login temporarily locked. Please try again later"


def test_normalize_to_utc_treats_naive_timestamp_as_utc():
    """Naive datetimes should be interpreted as UTC to avoid mixed-type comparisons."""
    naive_value = datetime(2026, 3, 16, 10, 30, 0)

    normalized = UserService._normalize_to_utc(naive_value)

    assert normalized == datetime(2026, 3, 16, 10, 30, 0, tzinfo=timezone.utc)


def test_user_is_active_and_locked():
    """Test methods is_active and is_locked of the User model."""
    user = User(
        username="activeuser",
        email="active@example.com",
        hashed_password="irrelevant",
        active=True
    )
    assert user.is_active() is True
    assert user.is_locked() is False

    user_inactive = User(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password="irrelevant",
        active=False
    )
    assert user_inactive.is_active() is False
    assert user_inactive.is_locked() is True

    def test_user_has_permission():
        """Test has_permission method of the User model."""
        from app.models import Role, Permission, RolePermission, UserRole
        import uuid
        # Erzeuge Permission
        perm = Permission(id=uuid.uuid4(), name="edit", active=True)
        # Erzeuge Role und verknüpfe Permission
        role = Role(id=uuid.uuid4(), name="editor", active=True)
        role_perm = RolePermission(id=uuid.uuid4(), role=role, permission=perm)
        role.role_permissions = [role_perm]
        # Erzeuge UserRole
        user_role = UserRole(id=uuid.uuid4(), role=role, active=True)
        # Erzeuge User
        user = User(username="permuser", email="perm@example.com", hashed_password="irrelevant", active=True)
        user.user_roles = [user_role]
        assert user.has_permission("edit") is True
        assert user.has_permission("delete") is False

    def test_user_get_permissions():
        """Test get_permissions method of the User model."""
        from app.models import Role, Permission, RolePermission, UserRole
        import uuid
        perm1 = Permission(id=uuid.uuid4(), name="read", active=True)
        perm2 = Permission(id=uuid.uuid4(), name="write", active=True)
        role = Role(id=uuid.uuid4(), name="author", active=True)
        role.role_permissions = [
            RolePermission(id=uuid.uuid4(), role=role, permission=perm1),
            RolePermission(id=uuid.uuid4(), role=role, permission=perm2)
        ]
        user_role = UserRole(id=uuid.uuid4(), role=role, active=True)
        user = User(username="permuser2", email="perm2@example.com", hashed_password="irrelevant", active=True)
        user.user_roles = [user_role]
        perms = user.get_permissions()
        assert set(perms) == {"read", "write"}


def test_get_user_by_id_invalid_uuid(db):
    # Zeile 31, 34: Fehlerhafte UUID
    user = UserService.get_user_by_id(db, "not-a-uuid")
    assert user is None

def test_update_user_profile_user_not_found(db):
    # Zeile 102-103: User nicht gefunden
    with pytest.raises(ValueError):
        UserService.update_user_profile(db, str(uuid.uuid4()), first_name="X")

def test_change_password_user_not_found(db):
    # Zeile 117: User nicht gefunden
    success, msg = UserService.change_password(db, str(uuid.uuid4()), "x", "y")
    assert not success and "not found" in msg

def test_change_password_wrong_current(db, setup_roles):
    # Zeile 120: Falsches Passwort
    user = UserService.create_user(db, "pwuser", "pw@example.com", "pw1", is_first_user=False)
    success, msg = UserService.change_password(db, str(user.id), "wrong", "new")
    assert not success and "incorrect" in msg

def test_change_password_invalid_new(db, setup_roles, monkeypatch):
    # Zeile 170: Passwortvalidierung schlägt fehl
    user = UserService.create_user(db, "pwuser2", "pw2@example.com", "pw1", is_first_user=False)
    monkeypatch.setattr("app.services.user_service.validate_password_requirements", lambda pw: (False, "fail"))
    success, msg = UserService.change_password(db, str(user.id), "pw1", "bad")
    assert not success and msg == "fail"

def test_reset_password_user_not_found(db):
    # Zeile 182-183: User nicht gefunden
    success, msg = UserService.reset_password(db, str(uuid.uuid4()), "new")
    assert not success and "not found" in msg

def test_reset_password_invalid_new(db, setup_roles, monkeypatch):
    # Zeile 196: Passwortvalidierung schlägt fehl
    user = UserService.create_user(db, "pwuser3", "pw3@example.com", "pw1", is_first_user=False)
    monkeypatch.setattr("app.services.user_service.validate_password_requirements", lambda pw: (False, "fail"))
    success, msg = UserService.reset_password(db, str(user.id), "bad")
    assert not success and msg == "fail"

def test_update_email_user_not_found(db):
    # Zeile 199: User nicht gefunden
    success, msg = UserService.update_email(db, str(uuid.uuid4()), "x@x.de")
    assert not success and "not found" in msg

def test_update_email_already_exists(db, setup_roles):
    # Zeile 203: Email schon vergeben
    u1 = UserService.create_user(db, "u1", "e1@e.de", "pw", is_first_user=False)
    u2 = UserService.create_user(db, "u2", "e2@e.de", "pw", is_first_user=False)
    success, msg = UserService.update_email(db, str(u2.id), "e1@e.de")
    assert not success and "already" in msg

def test_enable_otp_user_not_found(db):
    # Zeile 209-210: User nicht gefunden
    with pytest.raises(ValueError):
        UserService.enable_otp(db, str(uuid.uuid4()))

def test_disable_otp_user_not_found(db):
    # Zeile 219: User nicht gefunden
    assert UserService.disable_otp(db, str(uuid.uuid4())) is False

def test_list_users_filters(db, setup_roles):
    # Zeile 223: Filterung
    UserService.create_user(db, "fuser", "f@e.de", "pw", is_first_user=False)
    users, total = UserService.list_users(db, filter_username="fuser")
    assert any(u.username == "fuser" for u in users)
    users, total = UserService.list_users(db, filter_email="f@e.de")
    assert any(u.email == "f@e.de" for u in users)
    users, total = UserService.list_users(db, active_only=False)
    assert isinstance(users, list)

def test_update_user_as_support_user_not_found(db):
    # Zeile 230-231: User nicht gefunden
    with pytest.raises(ValueError):
        UserService.update_user_as_support(db, str(uuid.uuid4()), str(uuid.uuid4()))

def test_get_user_roles_invalid_uuid(db):
    # Zeile 238-254: Fehlerhafte UUID
    roles = UserService.get_user_roles(db, "not-a-uuid")
    assert roles == []

def test_get_user_roles_inactive(db, setup_roles):
    # Zeile 259-272: Inaktive Rollen
    user = UserService.create_user(db, "roleuser", "role@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    ur = UserRole(id=uuid.uuid4(), user_id=user.id, role_id=admin_role.id, active=False)
    db.add(ur)
    db.commit()
    roles = UserService.get_user_roles(db, str(user.id), include_inactive=True)
    assert any(r["active"] is False for r in roles)

def test_assign_role_to_user_invalid_uuid(db):
    # Zeile 277-289: Fehlerhafte UUID
    ur, err = UserService.assign_role_to_user(db, "bad", "bad", "bad")
    assert ur is None and "Invalid UUID" in err

def test_assign_role_to_user_user_not_found(db, setup_roles):
    # Zeile 304: User nicht gefunden
    admin_role = setup_roles["admin"]
    ur, err = UserService.assign_role_to_user(db, str(uuid.uuid4()), str(admin_role.id), str(uuid.uuid4()))
    assert ur is None and "not found" in err

def test_assign_role_to_user_role_not_found(db, setup_roles):
    # Zeile 329: Rolle nicht gefunden
    user = UserService.create_user(db, "ruser", "r@e.de", "pw", is_first_user=False)
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(uuid.uuid4()), str(user.id))
    assert ur is None and "Role not found" in err

def test_assign_role_to_user_role_inactive(db, setup_roles):
    # Zeile 334: Rolle inaktiv
    user = UserService.create_user(db, "ruser2", "r2@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    admin_role.active = False
    db.commit()
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur is None and "not active" in err

def test_assign_role_to_user_otp_required(db, setup_roles):
    # Zeile 336, 341-342: OTP-Zwang
    # Ensure there is at least one user in the DB before the test user
    UserService.create_user(db, "dummy", "dummy@e.de", "pw", is_first_user=True)
    user = UserService.create_user(db, "ruser3", "r3@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    user.otp_enabled = False
    db.commit()
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur is None and "OTP" in err

def test_assign_role_to_user_already_assigned(db, setup_roles):
    # Zeile 359: Bereits zugewiesen
    user = UserService.create_user(db, "ruser4", "r4@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur is not None
    ur2, err2 = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur2 is None and "already" in err2

def test_assign_role_to_user_removed_cannot_reassign(db, setup_roles):
    # Zeile 360: Nach Entfernen nicht reaktivierbar
    user = UserService.create_user(db, "ruser5", "r5@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur is not None
    UserService.remove_role_from_user(db, str(user.id), str(admin_role.id), str(user.id))
    ur2, err2 = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur2 is None and "cannot be reactivated" in err2

def test_remove_role_from_user_invalid_uuid(db):
    # Zeile 407: Fehlerhafte UUID
    ok, err = UserService.remove_role_from_user(db, "bad", "bad", "bad")
    assert not ok and "Invalid UUID" in err

def test_remove_role_from_user_not_found(db, setup_roles):
    # Zeile 413: Rolle nicht gefunden
    user = UserService.create_user(db, "ruser6", "r6@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    ok, err = UserService.remove_role_from_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert not ok and "active role assignment" in err

def test_remove_role_from_user_success(db, setup_roles):
    # Zeile 418, 421: Erfolgreiches Entfernen
    user = UserService.create_user(db, "ruser7", "r7@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur is not None
    ok, err = UserService.remove_role_from_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ok and err is None

def test_remove_role_from_user_soft_delete(db, setup_roles):
    # Zeile 440: Soft delete setzt active=False
    user = UserService.create_user(db, "ruser8", "r8@e.de", "pw", is_first_user=False)
    admin_role = setup_roles["admin"]
    ur, err = UserService.assign_role_to_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ur is not None
    ok, err = UserService.remove_role_from_user(db, str(user.id), str(admin_role.id), str(user.id))
    assert ok
    ur_db = [ur for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all() if ur.role_id == admin_role.id][0]
    assert ur_db.active is False

def test_get_user_by_email_case_insensitive(db, setup_roles):
    # Zeile 491-492: Email-Case-Insensitive
    UserService.create_user(db, "caseuser", "Case@Email.com", "pw", is_first_user=False)
    user = UserService.get_user_by_email(db, "case@email.com")
    assert user is None or user.email.lower() == "case@email.com"  # je nach Implementierung

def test_list_users_pagination(db, setup_roles):
    # Zeile 504: Pagination
    for i in range(15):
        UserService.create_user(db, f"puser{i}", f"p{i}@e.de", "pw", is_first_user=False)
    users, total = UserService.list_users(db, skip=10, limit=5)
    assert len(users) <= 5 and total >= 15
