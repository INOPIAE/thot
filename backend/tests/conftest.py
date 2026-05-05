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
    from app.models import Role, UserRole
    db.query(User).filter_by(username="testadmin").delete()
    db.commit()
    # Ensure an admin role exists
    admin_role = db.query(Role).filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(id=uuid.uuid4(), name="admin", description="Admin role")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
    # Create admin user
    user = User(
        id=uuid.uuid4(),
        username="testadmin",
        email="admin@example.com",
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
    # Link user to admin role
    user_role = UserRole(user_id=user.id, role_id=admin_role.id)
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
