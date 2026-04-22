# Suppress DeprecationWarning from reportlab (ast.NameConstant)
import pytest
pytestmark = pytest.mark.filterwarnings(
    "ignore:ast.NameConstant is deprecated and will be removed in Python 3.14; use ast.Constant instead:DeprecationWarning"
)

import tempfile
from pathlib import Path
from datetime import datetime
from app.services import pdf_watermark_service
import pytest

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def create_dummy_pdf(path: Path):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(100, 750, "Test PDF for Watermark")
    c.save()


def test_create_watermarked_pdf_without_logo(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    create_dummy_pdf(pdf_path)
    out_bytes = pdf_watermark_service.create_watermarked_pdf(
        source_pdf=pdf_path,
        username="unittest",
        downloaded_at=datetime(2026, 4, 15, 12, 0),
        record_name="TestRecord",
        record_signature="SIG123",
        record_pdf_url="https://example.com/test.pdf",
        page_text="1",
        watermark_image_path=None,
        watermark_copyright="(c) Test"
    )
    assert isinstance(out_bytes, bytes)
    assert len(out_bytes) > 1000  # Should produce a non-empty PDF


def test_create_watermarked_pdf_with_invalid_logo(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    create_dummy_pdf(pdf_path)
    fake_logo = tmp_path / "not_an_image.png"
    fake_logo.write_text("not an image")
    # Should not raise, just skip logo
    out_bytes = pdf_watermark_service.create_watermarked_pdf(
        source_pdf=pdf_path,
        username="unittest",
        downloaded_at=datetime(2026, 4, 15, 12, 0),
        record_name="TestRecord",
        record_signature="SIG123",
        record_pdf_url="https://example.com/test.pdf",
        page_text="1",
        watermark_image_path=fake_logo,
        watermark_copyright="(c) Test"
    )
    assert isinstance(out_bytes, bytes)
    assert len(out_bytes) > 1000
