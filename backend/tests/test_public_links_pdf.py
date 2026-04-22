"""
Tests for /api/v1/public-links/pdf/{encoded_id} endpoint (public record PDF link resolution).
"""
import pytest
from app.utils.public_links import encode_uuid_to_base62

def test_resolve_public_record_pdf_link_authenticated(client, db):
    user = _create_user_with_role(db, "public_pdf_user")
    record = _create_record_fixture(db, user.id)
    encoded_id = encode_uuid_to_base62(record.id)
    headers = _auth_headers_for_user(user)
    response = client.get(f"/api/v1/public-links/pdf/{encoded_id}", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == str(record.id)
    assert payload["encoded_record_id"] == encoded_id
    assert payload["target_api_url"].endswith(f"/pages-gallery")
    assert payload["frontend_record_path"].endswith(f"/pages-gallery")

def test_resolve_public_record_pdf_link_unauthenticated(client, db):
    user = _create_user_with_role(db, "public_pdf_user2")
    record = _create_record_fixture(db, user.id)
    encoded_id = encode_uuid_to_base62(record.id)
    # No auth headers
    response = client.get(f"/api/v1/public-links/pdf/{encoded_id}", headers={"Host": "localhost"})
    assert response.status_code == 403
    # payload = response.json()
    # assert payload["record_id"] == str(record.id)
    # assert payload["encoded_record_id"] == encoded_id
    # assert payload["target_api_url"].endswith(f"/pages-gallery")
    # assert payload["frontend_record_path"].endswith(f"/pages-gallery")

def test_resolve_public_record_pdf_link_invalid_id_unauthenticated(client):
    response = client.get("/api/v1/public-links/pdf/INVALIDID", headers={"Host": "localhost"})
    assert response.status_code == 403
    # assert "invalid" in response.json()["detail"].lower() or "invalid" in response.text.lower()

def test_resolve_public_record_pdf_link_invalid_id_authenticated(client, db):
    user = _create_user_with_role(db, "public_pdf_user2")
    headers = _auth_headers_for_user(user)
    response = client.get("/api/v1/public-links/pdf/INVALIDID",  headers=headers)
    assert response.status_code == 404
    assert "Record not found" in response.json()["detail"].lower() or "record not found" in response.text.lower()

# Reuse helpers from test_public_links.py
from tests.test_public_links import _create_user_with_role, _create_record_fixture, _auth_headers_for_user
