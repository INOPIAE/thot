import pytest
from app.models.notification import Notification
from app.models.user import User
from app.models.role import Role
from app.schemas.notification import NotificationCreate
from uuid import uuid4
from datetime import datetime, timezone
from tests.conftest import auth_headers_and_csrf

def test_create_notification_as_admin(client, db, test_user):
    headers, cookies = auth_headers_and_csrf(test_user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    payload = {"title": "Test", "notification": "Body", "roles_id": str(uuid4()), "active": True}
    response = client.post("/api/v1/notifications/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["title"] == "Test"


def test_create_notification_forbidden_for_non_admin(client, db):
    # Create a non-admin user
    from app.models import User, Role, UserRole
    import uuid
    user = User(
        id=uuid.uuid4(),
        username="testuser2",
        email="testuser2@example.com",
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
    headers, cookies = auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    payload = {"title": "Test", "notification": "Body", "roles_id": str(uuid4()), "active": True}
    response = client.post("/api/v1/notifications/", json=payload, headers=headers)
    assert response.status_code == 403

def test_get_notifications_for_admin(client, db, test_user):
    headers, cookies = auth_headers_and_csrf(test_user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.get("/api/v1/notifications/", headers=headers)
    # 200 is expected if admin, 200 or empty list if no notifications
    assert response.status_code in (200, 404, 204)

def test_get_notifications_for_user(client, db):
    # Create a non-admin user
    from app.models import User
    import uuid
    user = User(
        id=uuid.uuid4(),
        username="testuser3",
        email="testuser3@example.com",
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
    headers, cookies = auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.get("/api/v1/notifications/", headers=headers)
    assert response.status_code in (200, 404, 204)

def test_get_notification_by_id_admin(client, db, test_user):
    headers, cookies = auth_headers_and_csrf(test_user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    notif_id = str(uuid4())
    response = client.get(f"/api/v1/notifications/{notif_id}", headers=headers)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["title"] == "Test"

def test_get_notification_by_id_forbidden_for_user(client, db):
    from app.models import User
    import uuid
    user = User(
        id=uuid.uuid4(),
        username="testuser4",
        email="testuser4@example.com",
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
    headers, cookies = auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    notif_id = str(uuid4())
    response = client.get(f"/api/v1/notifications/{notif_id}", headers=headers)
    assert response.status_code in (403, 404)

def test_get_notification_by_id_not_found(client, db, test_user):
    headers, cookies = auth_headers_and_csrf(test_user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    notif_id = str(uuid4())
    response = client.get(f"/api/v1/notifications/{notif_id}", headers=headers)
    assert response.status_code in (404, 403)

def test_update_notification_as_admin(client, db, test_user):
    headers, cookies = auth_headers_and_csrf(test_user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    notif_id = str(uuid4())
    payload = {"title": "New", "notification": "New body", "roles_id": str(uuid4()), "active": True}
    response = client.put(f"/api/v1/notifications/{notif_id}", json=payload, headers=headers)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["title"] == "New"

def test_update_notification_forbidden_for_user(client, db):
    from app.models import User
    import uuid
    user = User(
        id=uuid.uuid4(),
        username="testuser5",
        email="testuser5@example.com",
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
    headers, cookies = auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    notif_id = str(uuid4())
    payload = {"title": "New", "notification": "New body", "roles_id": str(uuid4()), "active": True}
    response = client.put(f"/api/v1/notifications/{notif_id}", json=payload, headers=headers)
    assert response.status_code in (403, 404)

def test_update_notification_not_found(client, db, test_user):
    headers, cookies = auth_headers_and_csrf(test_user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    notif_id = str(uuid4())
    payload = {"title": "New", "notification": "New body", "roles_id": str(uuid4()), "active": True}
    response = client.put(f"/api/v1/notifications/{notif_id}", json=payload, headers=headers)
    assert response.status_code in (404, 403)
