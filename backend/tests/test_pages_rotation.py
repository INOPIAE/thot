import pytest
from app.models import Page
from app.routes import pages as pages_routes
from app.utils import create_access_token, hash_password
from app.middleware.csrf import CSRFMiddleware

# Hilfsfunktion: Auth-Header + CSRF-Token für Tests
def _auth_headers_and_csrf(user):
    token = create_access_token(str(user.id))
    csrf_token = CSRFMiddleware.generate_csrf_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
        "X-CSRF-Token": csrf_token,
    }
    cookies = {"csrf_token": csrf_token}
    return headers, cookies

def _create_user_with_role(db, username: str, role_name: str):
    from app.models import Role, User, UserRole
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name, description=f"{role_name} role")
        db.add(role)
        db.flush()
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("TestPassword123!"),
        active=True,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, active=True))
    db.commit()
    db.refresh(user)
    return user

def _create_record_fixture(db, created_by):
    from app.models import Restriction, WorkStatusArea, WorkStatus, Record
    import uuid
    restriction = Restriction(name=f"none-{uuid.uuid4()}")
    area = WorkStatusArea(area=f"page-{uuid.uuid4()}")
    db.add_all([restriction, area])
    db.flush()
    workstatus = WorkStatus(status=f"running-{uuid.uuid4()}", workstatus_area_id=area.id)
    db.add(workstatus)
    db.flush()
    record = Record(
        title="Rotation Test Record",
        description="record description",
        signature="rot-test",
        comment="comment",
        restriction_id=restriction.id,
        workstatus_id=workstatus.id,
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, restriction, workstatus

def test_create_page_with_rotation(client, db, tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "rot_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 4 >>\nstartxref\n180\n%%EOF"
    )
    # Rotation explizit setzen
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Rotierte Seite",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
            "rotation": 90,
        },
        files={
            "file": ("rot.pdf", pdf_bytes, "application/pdf"),
        },
    )
    print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 200
    payload = response.json()
    assert payload["rotation"] == 90
    # Default-Rotation (nicht gesetzt)
    response2 = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Default-Rotation",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("def.pdf", pdf_bytes, "application/pdf"),
        },
    )
    print("RESPONSE2:", response2.status_code, response2.text)
    assert response2.status_code == 200
    payload2 = response2.json()
    assert payload2["rotation"] == 0

def test_update_page_rotation(client, db, tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "rot_user2", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 4 >>\nstartxref\n180\n%%EOF"
    )
    # Erstellt Seite mit Rotation 0
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Update-Rotation",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("update.pdf", pdf_bytes, "application/pdf"),
        },
    )
    print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 200
    page_id = response.json()["id"]
    # Update Rotation auf 180
    # Hole die aktuelle Seite, um Pflichtfelder zu übernehmen
    get_response = client.get(f"/api/v1/pages/{page_id}", headers=headers)
    assert get_response.status_code == 200
    page_data = get_response.json()
    # Sende alle Pflichtfelder beim Update mit
    response2 = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": page_data["name"],
            "restriction_id": page_data["restriction_id"],
            "workstatus_id": page_data["workstatus_id"],
            "rotation": 180,
        },
    )
    print("RESPONSE2:", response2.status_code, response2.text)
    assert response2.status_code == 200
    payload2 = response2.json()
    assert payload2["rotation"] == 180
    # Ungültige Rotation
    response3 = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={"rotation": 45},
    )
    assert response3.status_code == 400 or response3.status_code == 422
