from pathlib import Path

import logging

from app.services.pdf_ocr_service import PdfOcrService
from config import config


class _Completed:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_ocrmypdf_skips_clean_without_unpaper(tmp_path, monkeypatch):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")

    captured = {}

    def _fake_run(cmd, check, capture_output, text, env):
        captured["cmd"] = cmd
        output_pdf.write_bytes(b"ok")
        return _Completed(returncode=0)

    monkeypatch.setattr(config, "get_ocrmypdf_binary", lambda: "ocrmypdf")
    monkeypatch.setattr(config, "get_tesseract_binary", lambda: "tesseract")
    monkeypatch.setattr(config, "get_ghostscript_binary", lambda: "gs")
    monkeypatch.setattr(config, "get_unpaper_binary", lambda: None)
    monkeypatch.setattr("app.services.pdf_ocr_service.subprocess.run", _fake_run)

    result = PdfOcrService._run_ocrmypdf(input_pdf, output_pdf)

    assert result is True
    assert "--clean" not in captured["cmd"]


def test_run_ocrmypdf_uses_clean_with_unpaper(tmp_path, monkeypatch):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")

    captured = {}

    def _fake_run(cmd, check, capture_output, text, env):
        captured["cmd"] = cmd
        output_pdf.write_bytes(b"ok")
        return _Completed(returncode=0)

    monkeypatch.setattr(config, "get_ocrmypdf_binary", lambda: "ocrmypdf")
    monkeypatch.setattr(config, "get_tesseract_binary", lambda: "tesseract")
    monkeypatch.setattr(config, "get_ghostscript_binary", lambda: "gs")
    monkeypatch.setattr(config, "get_unpaper_binary", lambda: "unpaper")
    monkeypatch.setattr("app.services.pdf_ocr_service.subprocess.run", _fake_run)

    result = PdfOcrService._run_ocrmypdf(input_pdf, output_pdf)

    assert result is True
    assert "--clean" in captured["cmd"]


def test_run_ocrmypdf_returns_false_without_tesseract(tmp_path, monkeypatch, caplog):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")

    def _fake_run(cmd, check, capture_output, text, env):
        raise AssertionError("subprocess.run should not be called when tesseract is missing")

    monkeypatch.setattr(config, "get_ocrmypdf_binary", lambda: "ocrmypdf")
    monkeypatch.setattr(config, "get_tesseract_binary", lambda: None)
    monkeypatch.setattr("app.services.pdf_ocr_service.subprocess.run", _fake_run)

    with caplog.at_level(logging.INFO):
        result = PdfOcrService._run_ocrmypdf(input_pdf, output_pdf)

    assert result is False
    assert "OCR fallback: missing Tesseract binary" in caplog.text
    assert "config_key=TESSERACT_BIN" in caplog.text


def test_run_ocrmypdf_returns_false_without_ghostscript(tmp_path, monkeypatch, caplog):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")

    def _fake_run(cmd, check, capture_output, text, env):
        raise AssertionError("subprocess.run should not be called when Ghostscript is missing")

    monkeypatch.setattr(config, "get_ocrmypdf_binary", lambda: "ocrmypdf")
    monkeypatch.setattr(config, "get_tesseract_binary", lambda: "tesseract")
    monkeypatch.setattr(config, "get_ghostscript_binary", lambda: None)
    monkeypatch.setattr("app.services.pdf_ocr_service.subprocess.run", _fake_run)

    with caplog.at_level(logging.INFO):
        result = PdfOcrService._run_ocrmypdf(input_pdf, output_pdf)

    assert result is False
    assert "OCR fallback: missing Ghostscript binary" in caplog.text
    assert "config_key=GS_BIN" in caplog.text


def test_run_ocrmypdf_logs_optional_unpaper_message(tmp_path, monkeypatch, caplog):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")

    def _fake_run(cmd, check, capture_output, text, env):
        output_pdf.write_bytes(b"ok")
        return _Completed(returncode=0)

    monkeypatch.setattr(config, "get_ocrmypdf_binary", lambda: "ocrmypdf")
    monkeypatch.setattr(config, "get_tesseract_binary", lambda: "tesseract")
    monkeypatch.setattr(config, "get_ghostscript_binary", lambda: "gs")
    monkeypatch.setattr(config, "get_unpaper_binary", lambda: None)
    monkeypatch.setattr("app.services.pdf_ocr_service.subprocess.run", _fake_run)

    with caplog.at_level(logging.INFO):
        result = PdfOcrService._run_ocrmypdf(input_pdf, output_pdf)

    assert result is True
    assert "optional dependency unavailable: unpaper" in caplog.text
    assert "continuing without --clean" in caplog.text


def test_process_origin_to_current_logs_import_context_on_fallback(tmp_path, monkeypatch, caplog):
    origin_dir = tmp_path / "Sample" / "origin"
    origin_dir.mkdir(parents=True)
    origin_pdf = origin_dir / "Seite_1.pdf"
    origin_pdf.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(config, "UPLOAD_DIRECTORY", tmp_path)
    monkeypatch.setattr(config, "OCR_PIPELINE_ENABLED", False)

    with caplog.at_level(logging.INFO):
        result = PdfOcrService.process_origin_to_current(
            "Sample/origin/Seite_1.pdf",
            import_id="import-123",
            page_id="page-456",
            record_id="record-789",
        )

    assert result.current_file_relative_path == "Sample/current/Seite_1_current.pdf"
    assert "import_id=import-123" in caplog.text
    assert "page_id=page-456" in caplog.text
    assert "record_id=record-789" in caplog.text
    assert "OCR fallback active; copied original PDF to current_file" in caplog.text


def test_run_ocrmypdf_treats_known_pikepdf_check_failure_as_success(tmp_path, monkeypatch, caplog):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    input_pdf.write_bytes(b"%PDF-1.4\n")

    def _fake_run(cmd, check, capture_output, text, env):
        output_pdf.write_bytes(b"ok")
        return _Completed(
            returncode=15,
            stderr="AttributeError: 'pikepdf._core.Pdf' object has no attribute 'check'",
        )

    monkeypatch.setattr(config, "get_ocrmypdf_binary", lambda: "ocrmypdf")
    monkeypatch.setattr(config, "get_tesseract_binary", lambda: "tesseract")
    monkeypatch.setattr(config, "get_ghostscript_binary", lambda: "gs")
    monkeypatch.setattr(config, "get_unpaper_binary", lambda: None)
    monkeypatch.setattr("app.services.pdf_ocr_service.subprocess.run", _fake_run)

    with caplog.at_level(logging.INFO):
        result = PdfOcrService._run_ocrmypdf(input_pdf, output_pdf)

    assert result is True
    assert "known pikepdf check incompatibility" in caplog.text
