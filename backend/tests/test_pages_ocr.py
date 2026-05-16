from tests.conftest import auth_headers_and_csrf
"""Unittests für den OCR-Start-Endpunkt /pages/{page_id}/start-ocr"""

import uuid
import pytest
from app.models import Page, Record, Restriction, Role, User, UserRole, WorkStatus, WorkStatusArea
from app.services.page_ocr_job_service import PageOcrJobService
from app.utils import create_access_token, hash_password
from config import config

from io import BytesIO
from types import SimpleNamespace
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


# Neue Hilfsfunktion: Auth-Header + CSRF für Tests
def _auth_headers_and_csrf(user: User):
    return auth_headers_and_csrf(user)

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
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(f"/api/v1/pages/{page.id}/start-ocr", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "OCR job started"
    assert called["page_id"] == str(page.id)
    assert called["record_id"] == str(record.id)

def test_start_ocr_job_forbidden_for_non_privileged_user(client, db, tmp_path):
    user = _create_user_with_role(db, "ocr_viewer", "user_view")
    record, restriction, workstatus, page = _create_record_and_page(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(f"/api/v1/pages/{page.id}/start-ocr", headers=headers)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

def test_start_ocr_job_page_not_found(client, db, tmp_path):
    user = _create_user_with_role(db, "ocr_admin2", "admin")
    fake_page_id = uuid.uuid4()
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(f"/api/v1/pages/{fake_page_id}/start-ocr", headers=headers)
    assert response.status_code == 404
    assert "Page not found" in response.json()["detail"]

def test_start_ocr_job_no_origin_file(client, db, tmp_path):
    user = _create_user_with_role(db, "ocr_admin3", "admin")
    record, restriction, workstatus, page = _create_record_and_page(db, user.id)
    page.orgin_file = None
    db.commit()
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(f"/api/v1/pages/{page.id}/start-ocr", headers=headers)
    assert response.status_code == 400
    assert "No origin file" in response.json()["detail"]


def test_schedule_page_ocr_async_preserves_existing_comment(db, monkeypatch):
    user = _create_user_with_role(db, "ocr_async_preserve", "admin")
    record, restriction, workstatus, page = _create_record_and_page(db, user.id)
    page.comment = "Bestehender Kommentar"
    db.commit()

    class SessionProxy:
        def __getattr__(self, name):
            return getattr(db, name)

        def close(self):
            return None

    class ImmediateExecutor:
        def submit(self, func, *args):
            func(*args)
            return SimpleNamespace()

    monkeypatch.setattr(PageOcrJobService, "should_process_inline", classmethod(lambda cls: False))
    monkeypatch.setattr(PageOcrJobService, "_ensure_executor", classmethod(lambda cls: ImmediateExecutor()))
    monkeypatch.setattr("app.services.page_ocr_job_service.SessionLocal", lambda: SessionProxy())
    monkeypatch.setattr(
        "app.services.page_ocr_job_service.PdfOcrService.process_origin_to_current",
        lambda *args, **kwargs: SimpleNamespace(current_file_relative_path="OCRTestSignature/current/test_current.pdf"),
    )
    monkeypatch.setattr(
        "app.routes.pages._update_page_comment_with_detected_page_number",
        lambda page_obj: setattr(page_obj, "comment", "Seite: 77"),
    )

    completed_inline = PageOcrJobService.schedule_page_ocr(
        str(page.id),
        str(record.id),
        preserve_comment=True,
        preserved_comment="Bestehender Kommentar",
    )

    assert completed_inline is False

    db.expire_all()
    updated_page = db.query(Page).filter(Page.id == page.id).first()
    assert updated_page is not None
    assert updated_page.current_file == "OCRTestSignature/current/test_current.pdf"
    assert updated_page.comment == "Bestehender Kommentar"
