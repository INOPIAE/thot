"""
Tests for record read/write permissions.
"""

import uuid

from app.models import Record, Restriction, Role, User, UserRole, WorkStatus, WorkStatusArea
from app.utils import create_access_token, hash_password


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


def _create_record_fixture(db, created_by) -> Record:
    restriction = Restriction(name=f"none-{uuid.uuid4()}")
    area = WorkStatusArea(area=f"record-{uuid.uuid4()}")
    db.add_all([restriction, area])
    db.flush()

    workstatus = WorkStatus(status=f"running-{uuid.uuid4()}", workstatus_area_id=area.id)
    db.add(workstatus)
    db.flush()

    record = Record(
        title="Read only test record",
        description="record description",
        signature="REC-001",
        comment="comment",
        restriction_id=restriction.id,
        workstatus_id=workstatus.id,
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_regular_user_can_read_record_by_id(client, db):
    regular_user = _create_user_with_role(db, "reader_user", "user")
    record = _create_record_fixture(db, regular_user.id)

    response = client.get(
        f"/api/v1/records/{record.id}",
        headers=_auth_headers_for_user(regular_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(record.id)


def test_regular_user_is_read_only_for_records(client, db):
    regular_user = _create_user_with_role(db, "readonly_user", "user")
    record = _create_record_fixture(db, regular_user.id)
    headers = _auth_headers_for_user(regular_user)

    create_response = client.post(
        "/api/v1/records",
        headers=headers,
        json={
            "title": "Should fail",
            "restriction_id": str(record.restriction_id),
            "workstatus_id": str(record.workstatus_id),
        },
    )
    assert create_response.status_code == 403

    update_response = client.put(
        f"/api/v1/records/{record.id}",
        headers=headers,
        json={"title": "Updated"},
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/api/v1/records/{record.id}",
        headers=headers,
    )
    assert delete_response.status_code == 403


def test_user_bibl_role_can_modify_records(client, db):
    power_user = _create_user_with_role(db, "editor_user", "user_bibl")
    base_record = _create_record_fixture(db, power_user.id)
    headers = _auth_headers_for_user(power_user)

    create_response = client.post(
        "/api/v1/records",
        headers=headers,
        json={
            "title": "Allowed create",
            "restriction_id": str(base_record.restriction_id),
            "workstatus_id": str(base_record.workstatus_id),
        },
    )
    assert create_response.status_code == 201
    created_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/records/{created_id}",
        headers=headers,
        json={"title": "Allowed update"},
    )
    assert update_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/records/{created_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200


def test_create_record_requires_typed_body_fields(client, db):
    power_user = _create_user_with_role(db, "typed_create_user", "user_bibl")
    headers = _auth_headers_for_user(power_user)

    response = client.post(
        "/api/v1/records",
        headers=headers,
        json={
            "title": "Missing required foreign keys",
        },
    )

    assert response.status_code == 422


def test_create_record_rejects_invalid_date_format(client, db):
    power_user = _create_user_with_role(db, "date_validation_user", "user_bibl")
    base_record = _create_record_fixture(db, power_user.id)
    headers = _auth_headers_for_user(power_user)

    response = client.post(
        "/api/v1/records",
        headers=headers,
        json={
            "title": "Date validation",
            "restriction_id": str(base_record.restriction_id),
            "workstatus_id": str(base_record.workstatus_id),
            "enter_date": "31-12-2025",
        },
    )

    assert response.status_code == 422


def test_create_and_update_record_return_typed_response_fields(client, db):
    power_user = _create_user_with_role(db, "typed_response_user", "user_bibl")
    base_record = _create_record_fixture(db, power_user.id)
    headers = _auth_headers_for_user(power_user)

    create_response = client.post(
        "/api/v1/records",
        headers=headers,
        json={
            "title": "Typed response create",
            "signature": "SIG-900",
            "signature2": "SIG-900-B",
            "subtitle": "A subtitle",
            "year": "2025",
            "edition": "2",
            "restriction_id": str(base_record.restriction_id),
            "workstatus_id": str(base_record.workstatus_id),
            "enter_date": "2025-01-31",
            "sort_out_date": "2025-12-31",
        },
    )

    assert create_response.status_code == 201
    created_payload = create_response.json()
    created_id = created_payload["id"]
    assert created_payload["title"] == "Typed response create"
    assert created_payload["signature2"] == "SIG-900-B"
    assert created_payload["subtitle"] == "A subtitle"
    assert created_payload["year"] == "2025"
    assert created_payload["edition"] == "2"
    assert created_payload["enter_date"] == "2025-01-31"
    assert created_payload["sort_out_date"] == "2025-12-31"
    assert "restriction" not in created_payload
    assert "workstatus" not in created_payload

    update_response = client.put(
        f"/api/v1/records/{created_id}",
        headers=headers,
        json={
            "title": "Typed response updated",
            "isbn": "9780000000000",
            "number_pages": "321",
            "bibl_nr": "BIB-77",
        },
    )

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["title"] == "Typed response updated"
    assert updated_payload["isbn"] == "9780000000000"
    assert updated_payload["number_pages"] == "321"
    assert updated_payload["bibl_nr"] == "BIB-77"

    get_response = client.get(
        f"/api/v1/records/{created_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["id"] == created_id
    assert get_payload["title"] == "Typed response updated"
    assert get_payload["isbn"] == "9780000000000"
