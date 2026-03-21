"""
Tests for public links and record QR-code routes.
"""

import uuid

from app.models import Record, Restriction, Role, User, UserRole, WorkStatus, WorkStatusArea
from app.utils import create_access_token, hash_password
from app.utils.public_links import encode_uuid_to_base62


def _create_user_with_role(db, username: str, role_name: str = "user") -> User:
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


def _create_record_fixture(db, created_by, signature: str = "REC-QR-001") -> Record:
    restriction = Restriction(name=f"none-{uuid.uuid4()}")
    area = WorkStatusArea(area=f"record-{uuid.uuid4()}")
    db.add_all([restriction, area])
    db.flush()

    workstatus = WorkStatus(status=f"running-{uuid.uuid4()}", workstatus_area_id=area.id)
    db.add(workstatus)
    db.flush()

    record = Record(
        title="QR test record",
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
    return record


def test_resolve_public_record_link_by_base62_id(client, db):
    user = _create_user_with_role(db, "public_link_user")
    record = _create_record_fixture(db, user.id)
    encoded_id = encode_uuid_to_base62(record.id)

    response = client.get(
        f"/api/v1/public-links/lit/{encoded_id}",
        headers={"Host": "localhost"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == str(record.id)
    assert payload["encoded_record_id"] == encoded_id
    assert payload["target_api_url"] == f"/api/v1/records/{record.id}"
    assert payload["frontend_record_path"] == f"/records/{record.id}"


def test_get_record_qr_code_contains_signature_and_public_link(client, db):
    user = _create_user_with_role(db, "qr_user")
    record = _create_record_fixture(db, user.id, signature="SIG-2026-001")

    response = client.get(
        f"/api/v1/public-links/records/{record.id}/qr-code",
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == str(record.id)
    assert payload["signature"] == "SIG-2026-001"
    assert payload["public_url"].endswith(f"/lit/{payload['encoded_record_id']}")
    assert payload["target_api_url"] == f"/api/v1/records/{record.id}"
    assert payload["qr_size_mm"] == 35
    assert isinstance(payload["qr_code"], str)
    assert len(payload["qr_code"]) > 20
