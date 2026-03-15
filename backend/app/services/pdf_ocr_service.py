"""OCR pipeline for turning uploaded PDFs into searchable PDFs.

Pipeline stages:
1) Scan (existing PDF/JPEG input)
2) OpenCV preprocessing
3) Lightweight page analysis
4) Optional engine hooks (Tesseract / Tesseract deu_latf / Kraken)
5) OCRmyPDF searchable output
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import fitz  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency behavior
    fitz = None

from config import config

logger = logging.getLogger(__name__)

try:
    import cv2  # type: ignore[import-not-found]
    import numpy as np
except Exception:  # pragma: no cover - optional dependency behavior
    cv2 = None
    np = None


@dataclass
class OcrPipelineResult:
    """Pipeline execution result."""

    current_file_relative_path: Optional[str]
    used_ocrmypdf: bool
    analysis_summary: str


class PdfOcrService:
    """Service to generate searchable PDFs from origin files."""

    @staticmethod
    def process_origin_to_current(origin_file_relative_path: Optional[str]) -> OcrPipelineResult:
        """Create a searchable PDF from orgin_file and return current_file path.

        If OCR dependencies are unavailable and OCR is not required,
        the origin file is copied to a *_current.pdf fallback.
        """
        if not origin_file_relative_path:
            return OcrPipelineResult(None, False, "no-origin-file")

        origin_path = (config.UPLOAD_DIRECTORY / origin_file_relative_path).resolve()
        if not origin_path.exists() or not origin_path.is_file():
            raise FileNotFoundError(f"Origin file not found: {origin_path}")

        # Preferred layout:
        # uploads/{signature}/origin/{file}.pdf -> uploads/{signature}/current/{file}_current.pdf
        origin_parent = origin_path.parent
        if origin_parent.name == "origin":
            base_dir = origin_parent.parent
        else:
            # Backward compatibility for older paths without explicit origin folder.
            base_dir = origin_parent

        current_dir = base_dir / "current"
        current_dir.mkdir(parents=True, exist_ok=True)
        current_path = current_dir / f"{origin_path.stem}_current.pdf"

        if not config.OCR_PIPELINE_ENABLED:
            shutil.copy2(origin_path, current_path)
            rel_path = str(current_path.relative_to(config.UPLOAD_DIRECTORY)).replace("\\", "/")
            return OcrPipelineResult(rel_path, False, "ocr-disabled")

        with tempfile.TemporaryDirectory(prefix="nlf-ocr-") as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            preprocessed_pdf = tmp_dir_path / "preprocessed.pdf"
            PdfOcrService._preprocess_pdf(origin_path, preprocessed_pdf)
            analysis_summary = PdfOcrService._analyze_pdf(preprocessed_pdf)

            # Optional non-blocking hook for handwriting-focused runs.
            if PdfOcrService._should_run_kraken(analysis_summary):
                PdfOcrService._try_run_kraken_hook(preprocessed_pdf, tmp_dir_path)

            used_ocr = PdfOcrService._run_ocrmypdf(preprocessed_pdf, current_path)
            if not used_ocr:
                if config.OCR_PIPELINE_REQUIRED:
                    raise RuntimeError(
                        "OCR pipeline is required but OCRmyPDF is not available or failed."
                    )
                shutil.copy2(origin_path, current_path)

        rel_path = str(current_path.relative_to(config.UPLOAD_DIRECTORY)).replace("\\", "/")
        return OcrPipelineResult(rel_path, used_ocr, analysis_summary)

    @staticmethod
    def _preprocess_pdf(input_pdf: Path, output_pdf: Path) -> None:
        """OpenCV preprocessing stage (fallbacks to source when unavailable)."""
        if fitz is None or cv2 is None or np is None:
            shutil.copy2(input_pdf, output_pdf)
            return

        src_doc = fitz.open(input_pdf)
        dst_doc = fitz.open()

        try:
            for page in src_doc:
                pix = page.get_pixmap(dpi=config.OCR_DPI, alpha=False)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

                if pix.n == 4:
                    bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
                else:
                    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

                gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
                denoised = cv2.fastNlMeansDenoising(gray, h=12)
                processed = cv2.adaptiveThreshold(
                    denoised,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    31,
                    7,
                )

                ok, encoded = cv2.imencode(".png", processed)
                if not ok:
                    raise RuntimeError("Failed to encode preprocessed page image")

                dst_page = dst_doc.new_page(width=page.rect.width, height=page.rect.height)
                dst_page.insert_image(dst_page.rect, stream=encoded.tobytes())

            dst_doc.save(output_pdf)
        finally:
            src_doc.close()
            dst_doc.close()

    @staticmethod
    def _analyze_pdf(pdf_path: Path) -> str:
        """Page analysis stage to summarize likely page type."""
        if fitz is None or cv2 is None or np is None:
            return "analysis-skipped-no-opencv"

        doc = fitz.open(pdf_path)
        try:
            page_kinds = []
            for page in doc:
                pix = page.get_pixmap(dpi=150, alpha=False)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY if pix.n == 3 else cv2.COLOR_BGRA2GRAY)
                edges = cv2.Canny(gray, 80, 180)
                edge_density = float(np.count_nonzero(edges)) / float(edges.size)

                # Heuristic only: lower edge density is often machine print.
                if edge_density < 0.04:
                    page_kinds.append("print")
                elif edge_density < 0.09:
                    page_kinds.append("mixed")
                else:
                    page_kinds.append("handwriting")

            return ",".join(page_kinds) if page_kinds else "analysis-empty"
        finally:
            doc.close()

    @staticmethod
    def _run_ocrmypdf(input_pdf: Path, output_pdf: Path) -> bool:
        """OCRmyPDF stage for generating searchable PDF."""
        ocrmypdf_bin = config.get_ocrmypdf_binary()
        if not ocrmypdf_bin:
            logger.warning("OCRmyPDF binary not found, using fallback for current_file")
            return False

        cmd = [
            ocrmypdf_bin,
            "--skip-text",
            "--deskew",
            "--clean",
            "--rotate-pages",
            "--optimize",
            "1",
            "--jobs",
            "1",
            "-l",
            config.OCR_LANGUAGES,
            str(input_pdf),
            str(output_pdf),
        ]

        try:
            run = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )
            if run.returncode != 0:
                logger.warning(
                    "OCRmyPDF failed (exit=%s): %s",
                    run.returncode,
                    (run.stderr or run.stdout or "").strip(),
                )
                return False
        except Exception as exc:
            logger.warning("OCRmyPDF execution failed: %s", exc)
            return False

        return output_pdf.exists() and output_pdf.stat().st_size > 0

    @staticmethod
    def _should_run_kraken(analysis_summary: str) -> bool:
        """Decide whether to run Kraken based on page analysis result."""
        if not config.KRAKEN_ENABLED:
            return False

        if not analysis_summary or analysis_summary in {"analysis-empty", "analysis-skipped-no-opencv"}:
            return False

        tokens = [token.strip() for token in analysis_summary.split(",") if token.strip()]
        if not tokens:
            return False

        handwriting_pages = sum(1 for token in tokens if token == "handwriting")
        total_pages = len(tokens)
        handwriting_ratio = handwriting_pages / float(total_pages)

        return (
            handwriting_pages >= max(1, config.KRAKEN_MIN_HANDWRITING_PAGES)
            and handwriting_ratio >= config.KRAKEN_MIN_HANDWRITING_RATIO
        )

    @staticmethod
    def _try_run_kraken_hook(input_pdf: Path, temp_dir: Path) -> None:
        """Optional Kraken hook for handwriting-heavy pages.

        This stage is intentionally best-effort and non-blocking.
        """
        kraken_bin = config.get_kraken_binary()
        if fitz is None or not kraken_bin:
            return

        try:
            doc = fitz.open(input_pdf)
            if len(doc) == 0:
                doc.close()
                return

            first_page = doc[0]
            pix = first_page.get_pixmap(dpi=250, alpha=False)
            preview_png = temp_dir / "kraken_preview.png"
            pix.save(preview_png)
            doc.close()

            cmd = [
                kraken_bin,
                "-i",
                str(preview_png),
                str(temp_dir / "kraken_preview.txt"),
                "binarize",
                "segment",
                "ocr",
            ]
            subprocess.run(cmd, check=False, capture_output=True, text=True)
        except Exception:
            # Non-blocking by design.
            logger.debug("Kraken hook skipped after error", exc_info=True)
