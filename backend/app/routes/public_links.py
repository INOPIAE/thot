"""
Public link and QR code routes for records.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Record
from app.utils.auth import get_current_user
from app.utils.public_links import (
    QR_CODE_SIZE_MM,
    build_record_public_url,
    build_record_qr_payload,
    decode_base62_to_uuid,
    encode_uuid_to_base62,
    generate_qr_code_base64,
)
from config import config

router = APIRouter(
    prefix="/public-links",
    tags=["public-links"],
)


def parse_uuid_value(value: str, field_name: str) -> UUID:
    """Normalize UUID values before using them in queries."""
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}",
        )


@router.get("/records/{record_id}/qr-code")
async def get_record_qr_code(
    record_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate QR code payload (signature + public frontend link) for one record."""
    parsed_record_id = parse_uuid_value(record_id, "record_id")
    record = db.query(Record).filter(Record.id == parsed_record_id, Record.active == True).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    public_url = build_record_public_url(record.id)
    payload = build_record_qr_payload(record.signature, public_url)
    logo_path = config.get_qr_code_logo_path()
    qr_code = generate_qr_code_base64(payload=payload, target_size_mm=QR_CODE_SIZE_MM, logo_path=logo_path)

    return {
        "record_id": str(record.id),
        "encoded_record_id": encode_uuid_to_base62(record.id),
        "signature": record.signature,
        "public_url": public_url,
        "target_api_url": f"/api/v1/records/{record.id}",
        "qr_code": qr_code,
        "qr_size_mm": QR_CODE_SIZE_MM,
    }


@router.get("/lit/{encoded_id}")
async def resolve_public_record_link(
    encoded_id: str,
    db: Session = Depends(get_db),
):
    """Resolve base62 record id used in frontend public links (/lit/{id})."""
    try:
        record_uuid = decode_base62_to_uuid(encoded_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    record = db.query(Record).filter(Record.id == record_uuid, Record.active == True).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    return {
        "record_id": str(record.id),
        "encoded_record_id": encoded_id,
        "target_api_url": f"/api/v1/records/{record.id}",
        "frontend_record_path": f"/records/{record.id}",
    }


@router.get("/pdf/{encoded_id}")
async def resolve_public_record_pdf_link(
    encoded_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Resolve base62 record id used in frontend public links (/pdf/{id})."""
    try:
        record_uuid = decode_base62_to_uuid(encoded_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    record = db.query(Record).filter(Record.id == record_uuid, Record.active == True).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    return {
        "record_id": str(record.id),
        "encoded_record_id": encoded_id,
        "target_api_url": f"/api/v1/records/{record.id}/pages-gallery",
        "frontend_record_path": f"/records/{record.id}/pages-gallery",
    }
