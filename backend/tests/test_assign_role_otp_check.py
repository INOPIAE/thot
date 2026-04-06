import pytest
from app.models import User, Role
from app.services.user_service import UserService
from uuid import uuid4
from datetime import datetime, timezone

def create_user(db, username, otp_enabled=False):
    user = User(
        id=uuid4(),
        username=username,
        email=f"{username}@example.com",
        hashed_password="$2b$12$1234567890123456789012abcdefghijklmno12345678901234567890",
        active=True,
        created_on=datetime.now(timezone.utc),
        current_language="de",
        otp_enabled=otp_enabled,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_role(db, name):
    role = Role(id=uuid4(), name=name, description=f"{name} role", active=True)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def test_assign_support_admin_role_requires_otp(db):
    # Leere DB, erster User
    user1 = create_user(db, "firstuser", otp_enabled=False)
    admin_role = create_role(db, "admin")
    support_role = create_role(db, "support")
    # Erster User darf admin/support bekommen, auch ohne OTP
    user_role, err = UserService.assign_role_to_user(db, str(user1.id), str(admin_role.id), str(user1.id))
    assert user_role is not None
    user_role2, err2 = UserService.assign_role_to_user(db, str(user1.id), str(support_role.id), str(user1.id))
    assert user_role2 is not None
    # Zweiter User ohne OTP darf KEIN support/admin bekommen
    user2 = create_user(db, "user2", otp_enabled=False)
    user_role3, err3 = UserService.assign_role_to_user(db, str(user2.id), str(support_role.id), str(user1.id))
    assert user_role3 is None
    assert "OTP" in err3
    # Mit OTP darf support/admin zugewiesen werden
    user2.otp_enabled = True
    db.commit()
    user_role4, err4 = UserService.assign_role_to_user(db, str(user2.id), str(support_role.id), str(user1.id))
    assert user_role4 is not None
    # Normale Rolle (user) darf immer zugewiesen werden
    user_role_obj = create_role(db, "user")
    user3 = create_user(db, "user3", otp_enabled=False)
    user_role5, err5 = UserService.assign_role_to_user(db, str(user3.id), str(user_role_obj.id), str(user1.id))
    assert user_role5 is not None
    # Cleanup
    for u in [user1, user2, user3]:
        db.delete(u)
    for r in [admin_role, support_role, user_role_obj]:
        db.delete(r)
    db.commit()
