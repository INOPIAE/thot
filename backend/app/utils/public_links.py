"""
Utilities for public record links and QR code generation.
"""

import base64
import io
from pathlib import Path
from typing import Optional
from uuid import UUID

import qrcode
import qrcode.constants
from PIL import Image

from config import config

_BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE62_BASE = len(_BASE62_ALPHABET)
QR_CODE_SIZE_MM = 35
QR_CODE_RENDER_DPI = 300


def encode_uuid_to_base62(record_id: UUID) -> str:
    """Encode a UUID into a compact base62 string."""
    number = record_id.int
    if number == 0:
        return _BASE62_ALPHABET[0]

    encoded = []
    while number > 0:
        number, remainder = divmod(number, _BASE62_BASE)
        encoded.append(_BASE62_ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode_base62_to_uuid(value: str) -> UUID:
    """Decode a base62 string back into a UUID."""
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError("Encoded record id is required")

    number = 0
    for character in normalized:
        try:
            digit = _BASE62_ALPHABET.index(character)
        except ValueError as exc:
            raise ValueError("Encoded record id contains invalid characters") from exc
        number = (number * _BASE62_BASE) + digit

    if number < 0 or number >= (1 << 128):
        raise ValueError("Encoded record id is out of range")

    return UUID(int=number)


def build_record_public_url(record_id: UUID) -> str:
    """Build the public frontend URL for a record."""
    encoded_id = encode_uuid_to_base62(record_id)
    return f"{config.FRONTEND_URL.rstrip('/')}/lit/{encoded_id}"


def build_record_qr_payload(signature: str | None, public_url: str) -> str:
    """Build QR payload containing signature and public link."""
    normalized_signature = (signature or "").strip()
    if not normalized_signature:
        return public_url
    return f"{normalized_signature}\n{public_url}"


_QR_LOGO_SIZE_PX = 72


def generate_qr_code_base64(
    payload: str,
    target_size_mm: int = QR_CODE_SIZE_MM,
    logo_path: Optional[Path] = None,
) -> str:
    """Generate a PNG QR code and return it as base64.

    When *logo_path* is provided the image is loaded, scaled to
    ``_QR_LOGO_SIZE_PX`` × ``_QR_LOGO_SIZE_PX`` pixels and centred on the
    QR module.  ERROR_CORRECT_H is used so up to 30 % of the QR data area
    can be covered without losing decodability.
    If logo loading fails for any reason the code is returned without a logo.
    """
    # H-level error correction is required when a logo covers part of the code
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        border=4,
        box_size=10,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    target_pixels = max(1, round((target_size_mm / 25.4) * QR_CODE_RENDER_DPI))
    # NEAREST keeps the hard QR pixel edges crisp
    image = image.resize((target_pixels, target_pixels), Image.Resampling.NEAREST)

    if logo_path is not None:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Scale logo to the configured pixel size using high-quality resampling
            logo = logo.resize((_QR_LOGO_SIZE_PX, _QR_LOGO_SIZE_PX), Image.Resampling.LANCZOS)
            # Paste centred; use the alpha channel as mask so transparency is respected
            pos_x = (target_pixels - _QR_LOGO_SIZE_PX) // 2
            pos_y = (target_pixels - _QR_LOGO_SIZE_PX) // 2
            image.paste(logo, (pos_x, pos_y), logo)
        except Exception:
            # If the logo cannot be loaded or composited, continue without it
            pass

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
