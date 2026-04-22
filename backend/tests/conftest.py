# sys.path-Workaround für app-Imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils import create_access_token
from app.middleware.csrf import CSRFMiddleware
from app.models import User


import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models import User
from uuid import uuid4
from datetime import datetime, timezone

# Globale Test-Utility für Auth-Header + CSRF-Token
def auth_headers_and_csrf(user: User):
    token = create_access_token(str(user.id))
    csrf_token = CSRFMiddleware.generate_csrf_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
        "X-CSRF-Token": csrf_token,
    }
    cookies = {"csrf_token": csrf_token}
    return headers, cookies

@pytest.fixture
def test_user(db):
    import uuid
    from app.models import Role, UserRole, Permission, RolePermission
    db.query(User).filter_by(username="testuser").delete()
    db.commit()
    # Ensure a role exists
    role = db.query(Role).filter_by(name="user_bibl").first()
    if not role:
        role = Role(id=uuid.uuid4(), name="user_bibl", description="Test Bibliotheksrolle")
        db.add(role)
        db.commit()
        db.refresh(role)
    # Ensure a permission exists
    permission = db.query(Permission).filter_by(name="view_records").first()
    if not permission:
        permission = Permission(id=uuid.uuid4(), name="view_records", description="View records")
        db.add(permission)
        db.commit()
        db.refresh(permission)
    # Ensure role-permission link
    role_perm = db.query(RolePermission).filter_by(role_id=role.id, permission_id=permission.id).first()
    if not role_perm:
        role_perm = RolePermission(role_id=role.id, permission_id=permission.id)
        db.add(role_perm)
        db.commit()
    # Create user
    user = User(
        id=uuid.uuid4() if not isinstance(getattr(User, 'id', None), str) else str(uuid.uuid4()),
        username="testuser",
        email="old@example.com",
        hashed_password="$2b$12$1234567890123456789012abcdefghijklmno12345678901234567890",
        current_language="de",
        active=True,
        created_by=None,
        created_on=datetime.now(timezone.utc),
        last_modified_by=None,
        last_modified_on=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Link user to role
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db.add(user_role)
    db.commit()
    yield user
    db.delete(user)
    db.commit()
"""
Pytest configuration
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# SQLite does not support the UUID column type natively; patch it to use CHAR(32)
SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "CHAR(32)"

from app.database import Base, get_db
import app.database as app_database
from app.main import app
from fastapi.testclient import TestClient


# Test database


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://localhost", headers={"Host": "localhost"}) as c:
        yield c
    app.dependency_overrides.clear()
