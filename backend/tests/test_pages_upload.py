"""Tests for page PDF upload handling."""

from io import BytesIO
import uuid

from PIL import Image
from pypdf import PdfReader, PdfWriter

from app.models import Page, Record, Restriction, Role, User, UserRole, WorkStatus, WorkStatusArea
from app.utils import create_access_token, hash_password
from config import config


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


def test_create_page_splits_multi_page_pdf_into_multiple_pages(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    user = _create_user_with_role(db, "page_split_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id)

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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

    create_response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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
        headers=_auth_headers_for_user(user),
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


def test_e2e_current_file_is_set_on_create_and_update(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    user = _create_user_with_role(db, "page_e2e_user", "admin")
    record, restriction, workstatus = _create_record_fixture(db, user.id, signature="E2E Signature")

    create_response = client.post(
        "/api/v1/pages",
        headers=_auth_headers_for_user(user),
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
        headers=_auth_headers_for_user(user),
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