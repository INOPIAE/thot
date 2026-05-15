"""Tests for page PDF upload handling."""

from io import BytesIO
from pathlib import Path
import uuid

from PIL import Image
from pypdf import PdfReader, PdfWriter
import pytest

from app.models import Page, Record, Restriction, Role, User, UserRole, WorkStatus, WorkStatusArea
from app.routes import pages as pages_routes
from app.services.page_ocr_job_service import PageOcrJobService
from app.services.pdf_ocr_service import PdfOcrService
from app.utils import create_access_token, hash_password
from app.middleware.csrf import CSRFMiddleware
from config import config


PAGE_NUMBER_SAMPLES_DIR = Path(__file__).parent / "fixtures" / "page_number_samples"


@pytest.fixture(autouse=True)
def inline_ocr_processing(monkeypatch, db):
    def _run_ocr_inline(page_id: str, record_id: str | None = None) -> bool:
        page = db.query(Page).filter(Page.id == uuid.UUID(str(page_id))).first()
        assert page is not None

        ocr_result = PdfOcrService.process_origin_to_current(
            page.orgin_file,
            import_id="test-inline-ocr",
            page_id=page_id,
            record_id=record_id,
        )
        page.current_file = ocr_result.current_file_relative_path
        pages_routes._update_page_comment_with_detected_page_number(page)
        db.commit()
        return True

    monkeypatch.setattr(config, "OCR_PIPELINE_ASYNC", False)
    monkeypatch.setattr(PageOcrJobService, "schedule_page_ocr", _run_ocr_inline)


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



# Hilfsfunktion: Auth-Header + CSRF-Token für Tests
def _auth_headers_and_csrf(user: User):
    token = create_access_token(str(user.id))
    csrf_token = CSRFMiddleware.generate_csrf_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Host": "localhost",
        "X-CSRF-Token": csrf_token,
    }
    cookies = {"csrf_token": csrf_token}
    return headers, cookies


def _create_record_fixture(db, created_by, signature: str = "  My Signature  "):
    restriction = Restriction(name=f"none-{uuid.uuid4()}")
    area = WorkStatusArea(area=f"page-{uuid.uuid4()}")
    db.add_all([restriction, area])
    db.flush()

    workstatus = WorkStatus(status=f"running-{uuid.uuid4()}", workstatus_area_id=area.id)
    db.add(workstatus)
    db.flush()

    record = Record(
        title="Page upload test record",
        description="record description",
        signature=signature,
        comment="comment",
        restriction_id=restriction.id,
        workstatus_id=workstatus.id,
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, restriction, workstatus


def _build_pdf(page_count: int) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=200, height=200)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _build_image_pdf(page_count: int) -> bytes:
    images = []
    for index in range(page_count):
        color = 255 - (index * 40)
        images.append(Image.new("RGB", (200, 200), color=(color, color, color)))

    buffer = BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:])
    return buffer.getvalue()


def _build_encrypted_pdf(page_count: int, password: str) -> bytes:
    reader = PdfReader(BytesIO(_build_pdf(page_count)))
    writer = PdfWriter()
    for pdf_page in reader.pages:
        writer.add_page(pdf_page)
    writer.encrypt(password)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_create_page_returns_pending_ocr_status_when_processing_is_backgrounded(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ASYNC", True)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", True)
    monkeypatch.setattr(config, "OCR_PIPELINE_REQUIRED", False)
    monkeypatch.setattr(PageOcrJobService, "schedule_page_ocr", lambda page_id, record_id=None: False)

    user = _create_user_with_role(db, "page_async_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Async Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Async Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("async.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_file"] is None
    assert payload["ocr_status"] == "pending"
    assert payload["location_file"].startswith("Async_Signature/origin/")


def test_create_page_splits_multi_page_pdf_into_multiple_pages(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_split_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Ignored for multi-page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("multi-page.pdf", _build_pdf(3), "application/pdf"),
        },
    )
    print(response.json())
    assert response.status_code == 200
    payload = response.json()
    assert payload["split_pdf"] is True
    assert payload["created_count"] == 3
    assert [item["name"] for item in payload["items"]] == ["Seite 1", "Seite 2", "Seite 3"]
    assert [item["location_file"] for item in payload["items"]] == [
        "My_Signature/origin/Seite_1.pdf",
        "My_Signature/origin/Seite_2.pdf",
        "My_Signature/origin/Seite_3.pdf",
    ]
    assert [item["current_file"] for item in payload["items"]] == [
        "My_Signature/current/Seite_1_current.pdf",
        "My_Signature/current/Seite_2_current.pdf",
        "My_Signature/current/Seite_3_current.pdf",
    ]

    pages = db.query(Page).filter(Page.record_id == record.id, Page.active == True).order_by(Page.created_on.asc()).all()
    assert [page.name for page in pages] == ["Seite 1", "Seite 2", "Seite 3"]

    for expected_name in ["Seite_1.pdf", "Seite_2.pdf", "Seite_3.pdf"]:
        file_path = tmp_path / "My_Signature" / "origin" / expected_name
        assert file_path.exists()
        reader = PdfReader(str(file_path))
        assert len(reader.pages) == 1

    for expected_name in ["Seite_1_current.pdf", "Seite_2_current.pdf", "Seite_3_current.pdf"]:
        file_path = tmp_path / "My_Signature" / "current" / expected_name
        assert file_path.exists()


def test_create_page_single_pdf_keeps_single_page_behavior(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_single_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Single Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Cover Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("single.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["split_pdf"] is False
    assert payload["created_count"] == 1
    assert payload["name"] == "Cover Page"
    assert payload["location_file"].startswith("Single_Signature/origin/Seite_")
    assert payload["location_file"].endswith(".pdf")
    assert payload["current_file"].startswith("Single_Signature/current/Seite_")
    assert payload["current_file"].endswith("_current.pdf")

    pages = db.query(Page).filter(Page.record_id == record.id, Page.active == True).all()
    assert len(pages) == 1
    assert pages[0].name == "Cover Page"


def test_create_page_splits_image_based_multi_page_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_scan_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Scan Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Scanned Input",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("scan input üß.pdf", _build_image_pdf(2), "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["split_pdf"] is True
    assert payload["created_count"] == 2
    assert [item["location_file"] for item in payload["items"]] == [
        "Scan_Signature/origin/Seite_1.pdf",
        "Scan_Signature/origin/Seite_2.pdf",
    ]


def test_create_page_ignores_original_filename_special_characters(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_filename_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature=" Special Signature ")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Named Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("  komisch äöü #?.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["split_pdf"] is False
    assert payload["location_file"].startswith("Special_Signature/origin/Seite_")
    assert payload["location_file"].endswith(".pdf")


def test_create_page_rejects_oversized_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "MAX_UPLOAD_SIZE", 128)
    user = _create_user_with_role(db, "page_large_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Too Large",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("large.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]


def test_create_page_rejects_corrupted_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_bad_pdf_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Broken PDF",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("broken.pdf", b"not a pdf", "application/pdf"),
        },
    )

    assert response.status_code == 400
    assert "Invalid PDF file" in response.json()["detail"]


def test_create_page_rejects_password_protected_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_locked_pdf_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Locked PDF",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("locked.pdf", _build_encrypted_pdf(2, "secret123"), "application/pdf"),
        },
    )

    assert response.status_code == 400
    assert "Invalid PDF file" in response.json()["detail"]


def test_update_page_rejects_multi_page_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_update_multi_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    create_response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Original Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("single.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert create_response.status_code == 200
    page_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "Original Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("multi.pdf", _build_pdf(2), "application/pdf"),
        },
    )

    assert update_response.status_code == 400
    assert "Only single-page PDFs are allowed" in update_response.json()["detail"]


def test_update_page_uploads_restriction_pdf_with_derived_filename(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    user = _create_user_with_role(db, "page_restriction_upload_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Restricted Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)

    create_response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Restricted Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("single.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert create_response.status_code == 200
    page_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "Restricted Page",
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "restriction_file": ("restriction.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["restriction_file"].startswith("Restricted_Signature/restriction/Seite_")
    assert payload["restriction_file"].endswith("_restricted.pdf")
    assert (tmp_path / payload["restriction_file"]).exists()

    persisted_page = db.query(Page).filter(Page.id == uuid.UUID(page_id)).first()
    assert persisted_page is not None
    assert persisted_page.restriction_file == payload["restriction_file"]

    view_response = client.get(f"/api/v1/pages/{page_id}/view-restriction-pdf", headers=headers)
    assert view_response.status_code == 200
    assert view_response.headers["content-type"] == "application/pdf"

    download_response = client.get(f"/api/v1/pages/{page_id}/download-restriction-pdf", headers=headers)
    assert download_response.status_code == 200
    assert "_restricted.pdf" in download_response.headers["content-disposition"]


def test_update_page_rejects_multi_page_restriction_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    user = _create_user_with_role(db, "page_restriction_multi_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)

    create_response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Restriction Target",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("single.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert create_response.status_code == 200
    page_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "Restriction Target",
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "restriction_file": ("restriction-multi.pdf", _build_pdf(2), "application/pdf"),
        },
    )

    assert update_response.status_code == 400
    assert "Only single-page PDFs are allowed" in update_response.json()["detail"]


def test_update_page_can_rotate_and_delete_restriction_pdf(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    user = _create_user_with_role(db, "page_restriction_rotate_delete_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Restricted Rotation Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)

    create_response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Restriction Rotate Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("single.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert create_response.status_code == 200
    page_id = create_response.json()["id"]

    upload_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "Restriction Rotate Page",
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
            "rotation_restriction": 90,
        },
        files={
            "restriction_file": ("restriction.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert upload_response.status_code == 200
    upload_payload = upload_response.json()
    assert upload_payload["restriction_file"]
    assert upload_payload["rotation_restriction"] == 90

    persisted_page = db.query(Page).filter(Page.id == uuid.UUID(page_id)).first()
    assert persisted_page is not None
    assert persisted_page.rotation_restriction == 90
    assert persisted_page.restriction_file is not None
    assert (tmp_path / persisted_page.restriction_file).exists()

    delete_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "Restriction Rotate Page",
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
            "rotation_restriction": 180,
            "delete_restriction_file": True,
        },
    )

    assert delete_response.status_code == 200
    delete_payload = delete_response.json()
    assert delete_payload["restriction_file"] is None
    assert delete_payload["rotation_restriction"] == 180

    db.expire_all()
    deleted_page = db.query(Page).filter(Page.id == uuid.UUID(page_id)).first()
    assert deleted_page is not None
    assert deleted_page.restriction_file is None
    assert deleted_page.rotation_restriction == 180


def test_gallery_endpoints_prefer_restriction_pdf_when_present(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    thumbnail_sources = []
    combined_sources = []

    def _fake_thumbnail_with_watermark(*, source_pdf, **kwargs):
        thumbnail_sources.append(Path(source_pdf).name)
        image = Image.new("RGB", (32, 32), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue()

    def _fake_watermarked_pdf(*, source_pdf, **kwargs):
        combined_sources.append(Path(source_pdf).name)
        return _build_pdf(1)

    monkeypatch.setattr(
        "app.services.pdf_watermark_service.create_thumbnail_with_watermark",
        _fake_thumbnail_with_watermark,
    )
    monkeypatch.setattr(
        "app.services.pdf_watermark_service.create_watermarked_pdf",
        _fake_watermarked_pdf,
    )

    user = _create_user_with_role(db, "page_gallery_restriction_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Gallery Restriction Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)

    create_response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Gallery Restriction Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("single.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert create_response.status_code == 200
    page_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "Gallery Restriction Page",
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "restriction_file": ("restriction.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert update_response.status_code == 200

    thumbnail_response = client.get(
        f"/api/v1/pages/{page_id}/thumbnail",
        headers=headers,
        params={"prefer_restriction": True},
    )
    assert thumbnail_response.status_code == 200
    assert thumbnail_sources
    assert thumbnail_sources[-1].endswith("_restricted.pdf")

    combined_response = client.get(
        f"/api/v1/records/{record.id}/download-combined-pdf",
        headers=headers,
    )
    assert combined_response.status_code == 200
    assert combined_sources
    assert combined_sources[-1].endswith("_restricted.pdf")


def test_e2e_current_file_is_set_on_create_and_update(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    user = _create_user_with_role(db, "page_e2e_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="E2E Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    create_response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "E2E Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("e2e-create.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert create_response.status_code == 200
    created_payload = create_response.json()
    page_id = created_payload["id"]
    assert created_payload["location_file"].startswith("E2E_Signature/origin/")
    assert created_payload["current_file"].startswith("E2E_Signature/current/")

    create_origin_path = tmp_path / created_payload["location_file"]
    create_current_path = tmp_path / created_payload["current_file"]
    assert create_origin_path.exists()
    assert create_current_path.exists()

    update_response = client.put(
        f"/api/v1/pages/{page_id}",
        headers=headers,
        data={
            "name": "E2E Page Updated",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("e2e-update.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["location_file"].startswith("E2E_Signature/origin/")
    assert updated_payload["current_file"].startswith("E2E_Signature/current/")

    update_origin_path = tmp_path / updated_payload["location_file"]
    update_current_path = tmp_path / updated_payload["current_file"]
    assert update_origin_path.exists()
    assert update_current_path.exists()

    persisted_page = db.query(Page).filter(Page.id == uuid.UUID(page_id)).first()
    assert persisted_page is not None
    assert persisted_page.current_file == updated_payload["current_file"]


def test_create_page_sets_comment_with_detected_page_number(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)
    monkeypatch.setattr(pages_routes, "_extract_page_number_from_pdf_text", lambda _: 42)

    user = _create_user_with_role(db, "page_number_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Number Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Numbered Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
            "comment": "Original comment",
        },
        files={
            "file": ("numbered.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["comment"] == "Seite: 42"


def test_create_page_sets_comment_when_page_number_not_found(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)
    monkeypatch.setattr(pages_routes, "_extract_page_number_from_pdf_text", lambda _: None)

    user = _create_user_with_role(db, "page_number_missing_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="Missing Number Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Number Missing Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("blank.pdf", _build_pdf(1), "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["comment"] == "Seite: nicht gefunden"


def test_extract_page_number_prefers_book_when_configured(monkeypatch):
    text = "Seite 77\n15"
    monkeypatch.setattr(config, "OCR_PAGE_NUMBER_PRIORITY", "book,stamp")

    result = pages_routes._extract_page_number_from_text(text)

    assert result == 77


def test_extract_page_number_prefers_stamp_when_configured(monkeypatch):
    text = "Seite 77\n15"
    monkeypatch.setattr(config, "OCR_PAGE_NUMBER_PRIORITY", "stamp,book")

    result = pages_routes._extract_page_number_from_text(text)

    assert result == 15


def test_extract_page_number_supports_roman_book_numbers(monkeypatch):
    text = "Page XII"
    monkeypatch.setattr(config, "OCR_PAGE_NUMBER_PRIORITY", "book,stamp")

    result = pages_routes._extract_page_number_from_text(text)

    assert result == 12


def test_extract_book_number_ignores_body_text_reference():
    """'Seite X' buried in a sentence must not be returned as the page number."""
    text = "Der Text verweist auf Seite 216 des nachfolgenden Bandes."

    result = pages_routes._extract_book_page_number_from_text(text)

    assert result is None


def test_extract_book_number_accepts_isolated_seite_label():
    """'Seite X' alone on its line must still be detected."""
    text = "Einleitung\nSeite 5\nAbschnitt"

    result = pages_routes._extract_book_page_number_from_text(text)

    assert result == 5


def test_extract_positional_page_number_finds_footer_number(tmp_path, monkeypatch):
    """Visitor returns a standalone number in the footer zone → returned as page number."""
    import pypdf

    class _FakeMediaBox:
        height = 842.0
        width = 595.0
        lower_left = (0.0, 0.0)
        upper_right = (595.0, 842.0)

    class _FakePage:
        mediabox = _FakeMediaBox()

        def extract_text(self, visitor_text=None):
            if visitor_text:
                # Body text at y ≈ 0.82 (middle/upper area)
                visitor_text("Fließtext auf Seite 77 des Kapitels", None, [1, 0, 0, 1, 72, 690], None, None)
                # Page number in footer at y ≈ 0.05
                visitor_text("42", None, [1, 0, 0, 1, 500, 40], None, None)
            return "Fließtext auf Seite 77 des Kapitels\n42"

    class _FakeReader:
        def __init__(self, path):
            self.pages = [_FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)
    monkeypatch.setattr("app.routes.pages.PdfReader", _FakeReader)
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    result = pages_routes._extract_positional_page_number_from_pdf("test.pdf")

    assert result == 42


def test_extract_positional_page_number_handles_digit_fragments(tmp_path, monkeypatch):
    """OCRmyPDF emits each digit separately; '2','1','6' at same y must be read as 216."""
    import pypdf

    class _FakeMediaBox:
        lower_left = (0.0, 0.0)
        upper_right = (595.0, 842.0)

    class _FakePage:
        mediabox = _FakeMediaBox()

        def extract_text(self, visitor_text=None):
            if visitor_text:
                # Three separate digit fragments in the footer zone
                visitor_text("2", None, [1, 0, 0, 1, 490, 38], None, None)
                visitor_text("1", None, [1, 0, 0, 1, 498, 38], None, None)
                visitor_text("6", None, [1, 0, 0, 1, 506, 38], None, None)
            return "216"

    class _FakeReader:
        def __init__(self, path):
            self.pages = [_FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)
    monkeypatch.setattr("app.routes.pages.PdfReader", _FakeReader)
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    result = pages_routes._extract_positional_page_number_from_pdf("test.pdf")

    assert result == 216


def test_extract_positional_page_number_prefers_right_footer_zone(tmp_path, monkeypatch):
    """When footer has multiple numbers, right-footer stamp should win."""
    import pypdf

    class _FakeMediaBox:
        lower_left = (0.0, 0.0)
        upper_right = (595.0, 842.0)

    class _FakePage:
        mediabox = _FakeMediaBox()

        def extract_text(self, visitor_text=None):
            if visitor_text:
                # Left/footer noise
                visitor_text("12", None, [1, 0, 0, 1, 40, 35], None, None)
                # Right/footer page number
                visitor_text("216", None, [1, 0, 0, 1, 520, 35], None, None)
            return "12\n216"

    class _FakeReader:
        def __init__(self, path):
            self.pages = [_FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)
    monkeypatch.setattr("app.routes.pages.PdfReader", _FakeReader)
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    result = pages_routes._extract_positional_page_number_from_pdf("test.pdf")

    assert result == 216


def test_extract_stamp_page_number_allows_punctuation():
    """Standalone footer numbers wrapped in punctuation should still match."""
    text = "... 216 ."

    result = pages_routes._extract_stamp_page_number_from_text(text)

    assert result == 216


def test_extract_stamp_page_number_supports_zero_and_ocr_confusions():
    """Right-footer stamps may be OCR'd as 000001 or 00000C and must still parse."""
    assert pages_routes._extract_stamp_page_number_from_text("000001") == 1
    assert pages_routes._extract_stamp_page_number_from_text("000003") == 3
    assert pages_routes._extract_stamp_page_number_from_text("0 0 0 0 0 3") == 3
    assert pages_routes._extract_stamp_page_number_from_text("00000C") == 0


def test_extract_page_number_uses_image_footer_when_text_methods_fail(monkeypatch):
    monkeypatch.setattr(pages_routes, "_extract_positional_page_number_from_pdf", lambda _: None)
    monkeypatch.setattr(pages_routes, "_extract_page_number_from_pdf_image_footer", lambda _: 3)

    result = pages_routes._extract_page_number_from_pdf_text("dummy.pdf")

    assert result == 3


def test_extract_page_number_prefers_image_footer_stamp_over_positional_result(monkeypatch):
    """Zero-padded footer stamps should win over weaker positional OCR results."""
    monkeypatch.setattr(pages_routes, "_extract_page_number_from_pdf_image_footer", lambda _: 3)
    monkeypatch.setattr(pages_routes, "_extract_positional_page_number_from_pdf", lambda _: 2)

    result = pages_routes._extract_page_number_from_pdf_text("dummy.pdf")

    assert result == 3


def test_page_number_fixture_manifest_matches_available_files():
    """Keep the OCR sample fixture corpus stable when example PDFs are swapped."""
    available_files = {pdf_file.name for pdf_file in PAGE_NUMBER_SAMPLES_DIR.glob("*.pdf")}

    assert available_files == {
        "scan_handwriting_right_bottom_stamp_expected_0.pdf",
        "scan_handwriting_right_bottom_stamp_expected_1.pdf",
        "scan_printed_right_bottom_stamp_expected_0.pdf",
        "scan_printed_right_bottom_stamp_expected_2.pdf",
        "scan_printed_right_bottom_stamp_expected_3.pdf",
        "scan_right_bottom_expected_3.pdf",
    }


def test_extract_positional_page_number_skips_body_reference(tmp_path, monkeypatch):
    """Body reference 'Seite 77' must not be returned; only the footer number wins."""
    import pypdf

    class _FakeMediaBox:
        height = 842.0
        width = 595.0
        lower_left = (0.0, 0.0)
        upper_right = (595.0, 842.0)

    class _FakePage:
        mediabox = _FakeMediaBox()

        def extract_text(self, visitor_text=None):
            if visitor_text:
                # "Seite 77" in a body sentence at y ≈ 0.82 — must NOT match
                visitor_text("Text der auf Seite 77 verweist.", None, [1, 0, 0, 1, 72, 690], None, None)
            return "Text der auf Seite 77 verweist."

    class _FakeReader:
        def __init__(self, path):
            self.pages = [_FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)
    monkeypatch.setattr("app.routes.pages.PdfReader", _FakeReader)
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    result = pages_routes._extract_positional_page_number_from_pdf("test.pdf")

    assert result is None


def test_create_and_get_page_with_order_by(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "order_by_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="OrderBy Signature")
    headers, cookies = _auth_headers_and_csrf(user)
    # Erstelle eine Seite mit explizitem order_by
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "OrderBy Page",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
            "order_by": 7,
        },
        files={
            "file": ("orderby.pdf", _build_pdf(1), "application/pdf"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "order_by" in payload
    assert payload["order_by"] == 7
    page_id = payload["id"]

    # Hole die Seite und prüfe order_by
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    get_response = client.get(f"/api/v1/pages/{page_id}", headers=headers)
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert "order_by" in get_payload
    assert get_payload["order_by"] == 7

def test_create_page_rollback_on_error_during_split(client, db, tmp_path, monkeypatch):
    """Testet, dass bei Fehler in der for-Schleife alle angelegten Dateien gelöscht werden (Rollback)."""
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    # Patch PageService.create_page, um beim zweiten Aufruf einen Fehler zu werfen
    import app.services.page_service as page_service_mod
    call_count = {"count": 0}
    orig_create_page = page_service_mod.PageService.create_page
    def fail_on_second(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 2:
            raise Exception("Simulierter Fehler bei Seite 2")
        return orig_create_page(*args, **kwargs)
    monkeypatch.setattr(page_service_mod.PageService, "create_page", fail_on_second)

    user = _create_user_with_role(db, "rollback_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="RollbackTest")
    headers, cookies = _auth_headers_and_csrf(user)
    client.cookies.clear()
    for k, v in cookies.items():
        client.cookies.set(k, v)
    response = client.post(
        "/api/v1/pages",
        headers=headers,
        data={
            "name": "Should trigger rollback",
            "record_id": str(record.id),
            "restriction_id": str(restriction.id),
            "workstatus_id": str(workstatus.id),
        },
        files={
            "file": ("multi-page.pdf", _build_pdf(3), "application/pdf"),
        },
    )
    # Es muss ein Fehler auftreten
    assert response.status_code == 400
    # Es dürfen keine Dateien im Upload-Verzeichnis liegen
    files = list(tmp_path.rglob("*"))
    # Nur das tmp_path selbst darf existieren, keine Dateien
    assert all(f.is_dir() for f in files), f"Es wurden Dateien nicht gelöscht: {files}"
    # Die Fehlernachricht muss den simulierten Fehler enthalten
    assert "Simulierter Fehler bei Seite 2" in response.text

