"""Unittests für den OCR-Start-Endpunkt /pages/{page_id}/start-ocr"""

import uuid
import pytest
from app.models import Page, Record, Restriction, Role, User, UserRole, WorkStatus, WorkStatusArea
from app.services.page_ocr_job_service import PageOcrJobService
from app.utils import create_access_token, hash_password
from config import config

from io import BytesIO
from pypdf import PdfWriter

def _create_user_with_role(db, username: str, role_name: str) -> User:
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

def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(str(user.id))
    return {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
    }

def _create_record_and_page(db, user_id) -> tuple[Record, Restriction, WorkStatus, Page]:
    restriction = Restriction(name=f"none-{uuid.uuid4()}")
    area = WorkStatusArea(area=f"page-{uuid.uuid4()}")
    db.add_all([restriction, area])
    db.flush()
    workstatus = WorkStatus(status=f"running-{uuid.uuid4()}", workstatus_area_id=area.id)
    db.add(workstatus)
    db.flush()
    record = Record(
        title="OCR Test Record",
        description="record description",
        signature="OCRTestSignature",
        comment="comment",
        restriction_id=restriction.id,
        workstatus_id=workstatus.id,
        created_by=user_id,
    )
    db.add(record)
    db.flush()
    # Erzeuge eine PDF-Datei
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()
    # Lege Page an
    page = Page(
        name="OCR Test Page",
        record_id=record.id,
        restriction_id=restriction.id,
        workstatus_id=workstatus.id,
        orgin_file="OCRTestSignature/origin/test.pdf",
        location_file="OCRTestSignature/origin/test.pdf",
        current_file=None,
        active=True,
    )
    db.add(page)
    db.commit()
    db.refresh(record)
    db.refresh(page)
    return record, restriction, workstatus, page

def test_start_ocr_job_success(client, db, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "ocr_admin", "admin")
    record, restriction, workstatus, page = _create_record_and_page(db, user.id)
    # Patch OCR-Job-Service, damit kein echter OCR-Job läuft
    called = {}
    def fake_schedule_page_ocr(page_id, record_id=None):
        called["page_id"] = page_id
        called["record_id"] = record_id
        return True
    monkeypatch.setattr(PageOcrJobService, "schedule_page_ocr", fake_schedule_page_ocr)
    response = client.post(f"/api/v1/pages/{page.id}/start-ocr", headers=_auth_headers_for_user(user))
    assert response.status_code == 200
    assert response.json()["message"] == "OCR job started"
    assert called["page_id"] == str(page.id)
    assert called["record_id"] == str(record.id)

def test_start_ocr_job_forbidden_for_non_privileged_user(client, db, tmp_path):
    user = _create_user_with_role(db, "ocr_viewer", "user_view")
    record, restriction, workstatus, page = _create_record_and_page(db, user.id)
    response = client.post(f"/api/v1/pages/{page.id}/start-ocr", headers=_auth_headers_for_user(user))
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

def test_start_ocr_job_page_not_found(client, db, tmp_path):
    user = _create_user_with_role(db, "ocr_admin2", "admin")
    fake_page_id = uuid.uuid4()
    response = client.post(f"/api/v1/pages/{fake_page_id}/start-ocr", headers=_auth_headers_for_user(user))
    assert response.status_code == 404
    assert "Page not found" in response.json()["detail"]

def test_start_ocr_job_no_origin_file(client, db, tmp_path):
    user = _create_user_with_role(db, "ocr_admin3", "admin")
    record, restriction, workstatus, page = _create_record_and_page(db, user.id)
    page.orgin_file = None
    db.commit()
    response = client.post(f"/api/v1/pages/{page.id}/start-ocr", headers=_auth_headers_for_user(user))
    assert response.status_code == 400
    assert "No origin file" in response.json()["detail"]
