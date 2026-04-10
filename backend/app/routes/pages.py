


"""
Pages API routes
"""

from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from io import BytesIO
import logging
import re
import subprocess
import tempfile
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from pypdf import PdfReader, PdfWriter

from app.database import get_db
from app.models.page import Page
from app.models.record import Record
from app.models.restriction import Restriction
from app.models.workstatus import WorkStatus
from app.services.page_ocr_job_service import PageOcrJobService
from app.services import pdf_ocr_service as pdf_ocr_module
from app.utils.auth import get_current_user
from config import config

router = APIRouter(prefix="/pages", tags=["pages"])
logger = logging.getLogger(__name__)


# OCR-Job manuell starten

@router.post("/{page_id}/start-ocr")
async def start_ocr_job(
    page_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Manually start OCR job for a page (admin/user_scan only)
    """
    if not (current_user.has_role("admin") or current_user.has_role("user_scan")):
        raise HTTPException(status_code=403, detail="Not authorized to start OCR job")

    import uuid
    try:
        page_uuid = uuid.UUID(page_id) if not isinstance(page_id, uuid.UUID) else page_id
    except Exception:
        raise HTTPException(status_code=404, detail="Page not found")

    page = db.query(Page).filter(Page.id == page_uuid, Page.active == True).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if not page.orgin_file:
        raise HTTPException(status_code=400, detail="No origin file for this page")

    try:
        PageOcrJobService.schedule_page_ocr(page_id=str(page.id), record_id=str(page.record_id) if page.record_id else None)
    except Exception as exc:
        logger.exception("Failed to start OCR job")
        raise HTTPException(status_code=500, detail=f"Failed to start OCR job: {str(exc)}")

    return {"message": "OCR job started"}

ALLOWED_PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
}

# Ensure upload directory exists
config.ensure_upload_directory()


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(config.ALLOWED_FILE_EXTENSIONS)}"
        )

    # Validate MIME type when provided by the client.
    if file.content_type and file.content_type.lower() not in ALLOWED_PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )


def _build_signature_folder_name(record_signature: Optional[str], record_id: str) -> str:
    """Create a filesystem-safe folder name from record signature."""
    if record_signature:
        normalized_signature = "_".join(record_signature.strip().split())
        safe_signature = "".join(
            char if char.isalnum() or char in {"_", "-"} else "_"
            for char in normalized_signature
        )
        safe_signature = safe_signature.strip("_")
        if safe_signature:
            return safe_signature
    return str(record_id)


def _build_safe_page_filename(page_name: str) -> str:
    """Create a filesystem-safe PDF filename from a page name."""
    normalized_name = "_".join((page_name or "Seite").strip().split())
    safe_name = "".join(
        char if char.isalnum() or char in {"_", "-"} else "_"
        for char in normalized_name
    ).strip("_")
    if not safe_name:
        safe_name = "Seite"
    return f"{safe_name}.pdf"


def _save_pdf_content(
    pdf_content: bytes,
    record_signature: Optional[str],
    record_id: str,
    filename: str,
    storage_subdir: str = "origin",
) -> str:
    """Persist PDF content and return the relative path used for storage."""
    # Create directory structure: uploads/{signature_folder}/{storage_subdir}/
    signature_folder = _build_signature_folder_name(record_signature, record_id)
    record_dir = config.UPLOAD_DIRECTORY / signature_folder / storage_subdir
    record_dir.mkdir(parents=True, exist_ok=True)

    file_path = record_dir / filename

    if len(pdf_content) > config.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {config.MAX_UPLOAD_SIZE / (1024*1024)}MB"
        )

    # Save file
    with open(file_path, "wb") as f:
        f.write(pdf_content)

    # Return relative path for database storage
    return f"{signature_folder}/{storage_subdir}/{filename}"


def save_uploaded_file(file: UploadFile, record_signature: Optional[str], record_id: str) -> str:
    """Save a single uploaded file to disk and return relative path."""
    filename = f"Seite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return _save_pdf_content(file.file.read(), record_signature, record_id, filename, storage_subdir="origin")


def _split_pdf_pages(pdf_content: bytes) -> list[bytes]:
    """Split a PDF into single-page PDFs."""
    try:
        reader = PdfReader(BytesIO(pdf_content))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF files are not supported")

        if len(reader.pages) <= 1:
            return [pdf_content]

        pages: list[bytes] = []
        for pdf_page in reader.pages:
            writer = PdfWriter()
            writer.add_page(pdf_page)
            buffer = BytesIO()
            writer.write(buffer)
            pages.append(buffer.getvalue())
        return pages
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PDF file: {str(exc)}"
        )


def _check_single_page_pdf(pdf_content: bytes) -> None:
    """Raise HTTP 400 if the PDF has more than one page (used for update/edit validation)."""
    try:
        reader = PdfReader(BytesIO(pdf_content))
        if reader.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file: Encrypted PDF files are not supported",
            )
        if len(reader.pages) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only single-page PDFs are allowed when updating an existing page. "
                       f"The uploaded file has {len(reader.pages)} pages.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PDF file: {str(exc)}",
        )



def _serialize_page(page) -> dict:
    """Serialize page response payload."""
    return {
        "id": str(page.id),
        "name": page.name,
        "description": page.description,
        "page": page.page,
        "comment": page.comment,
        "record_id": str(page.record_id),
        "orgin_file": page.orgin_file,
        "location_file": page.location_file,
        "current_file": page.current_file,
        "ocr_status": _get_ocr_status(page),
        "restriction_file": page.restriction_file,
        "restriction_id": str(page.restriction_id),
        "workstatus_id": str(page.workstatus_id) if page.workstatus_id else None,
        "created_on": page.created_on.isoformat() if page.created_on else None,
    }


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    """Parse a UUID form/path value and raise a request error when invalid."""
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}",
        )


def delete_uploaded_file(location_file: str) -> None:
    """Delete file from disk"""
    if location_file:
        file_path = config.UPLOAD_DIRECTORY / location_file
        if file_path.exists():
            file_path.unlink()


def _get_preferred_pdf_file(page: Page) -> Optional[str]:
    """Use searchable current_file when available, fallback to orgin_file."""
    return page.current_file or page.location_file


def _get_ocr_status(page: Page) -> str:
    """Return derived OCR processing status for API responses."""
    if not page.orgin_file:
        return "not-applicable"
    if page.current_file:
        return "completed"
    return "pending"


def _extract_text_from_pdf_first_page(file_relative_path: Optional[str]) -> str:
    """Extract text from the first PDF page for page-number detection."""
    if not file_relative_path:
        return ""

    pdf_path = (config.UPLOAD_DIRECTORY / file_relative_path).resolve()
    if not pdf_path.exists() or not pdf_path.is_file():
        return ""

    try:
        reader = PdfReader(str(pdf_path))
        if len(reader.pages) == 0:
            return ""
        return reader.pages[0].extract_text() or ""
    except Exception:
        return ""


def _roman_to_int(roman: str) -> Optional[int]:
    """Convert a roman numeral to integer, returning None on invalid input."""
    if not roman:
        return None

    roman = roman.upper()
    if not re.fullmatch(r"[IVXLCDM]+", roman):
        return None

    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for char in reversed(roman):
        value = values[char]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value

    # Canonical round-trip validation.
    if _int_to_roman(total) != roman:
        return None
    return total


def _int_to_roman(number: int) -> str:
    """Convert integer to roman numeral."""
    if number <= 0:
        return ""

    symbols = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    result = []
    remainder = number
    for value, symbol in symbols:
        while remainder >= value:
            result.append(symbol)
            remainder -= value
    return "".join(result)


def _extract_book_page_number_from_text(text: str) -> Optional[int]:
    """Extract likely book page number from OCR text."""
    normalized_text = (text or "").replace("\r\n", "\n")
    if not normalized_text.strip():
        return None

    def _check_line_isolated(m: re.Match) -> bool:
        """Return True when the match dominates its line (≤ 10 other chars)."""
        line_start = normalized_text.rfind("\n", 0, m.start()) + 1
        line_end_raw = normalized_text.find("\n", m.end())
        line_end = line_end_raw if line_end_raw != -1 else len(normalized_text)
        line = normalized_text[line_start:line_end]
        other = (line[: m.start() - line_start] + line[m.end() - line_start :]).strip()
        return len(other) <= 10

    # Strong label-based patterns — require the label to dominate its line so that
    # body-text references like "auf Seite 216 des Bandes" are not mistaken for
    # a page number in a header or footer.
    for match in re.finditer(r"\b(?:seite|page|p\.?)[\s.:\-]*(\d{1,4})\b", normalized_text, flags=re.IGNORECASE):
        number = int(match.group(1))
        if 1 <= number <= 9999 and _check_line_isolated(match):
            return number

    for match in re.finditer(
        r"\b(?:seite|page|p\.?)[\s.:\-]*([ivxlcdm]{1,8})\b",
        normalized_text,
        flags=re.IGNORECASE,
    ):
        roman_number = _roman_to_int(match.group(1))
        if roman_number and 1 <= roman_number <= 9999 and _check_line_isolated(match):
            return roman_number

    # Common book notation: current/total.
    for match in re.finditer(r"\b(\d{1,4})\s*/\s*\d{1,4}\b", normalized_text):
        number = int(match.group(1))
        if 1 <= number <= 9999:
            return number

    return None


def _extract_stamp_page_number_from_text(text: str) -> Optional[int]:
    """Extract likely stamped page number from OCR text."""
    normalized_text = (text or "").replace("\r\n", "\n")
    if not normalized_text.strip():
        return None

    def _normalize_numeric_token(token: str) -> Optional[int]:
        cleaned = token.strip()
        if not cleaned:
            return None

        translation = str.maketrans(
            {
                "O": "0",
                "o": "0",
                "D": "0",
                "Q": "0",
                "G": "0",
                "C": "0",
                "U": "0",
                "I": "1",
                "l": "1",
                "|": "1",
                "!": "1",
            }
        )
        normalized = cleaned.translate(translation)
        if not re.fullmatch(r"\d{1,6}", normalized):
            return None

        value = int(normalized.lstrip("0") or "0")
        if 0 <= value <= 999:
            return value
        return None

    for line in normalized_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Typical stamp: standalone number in footer/header.
        pure_number = re.fullmatch(r"[\[(\-\s.,;:]*([0-9]{1,4})[\])\-\s.,;:]*", stripped)
        if pure_number:
            number = int(pure_number.group(1))
            # Avoid matching years too aggressively in generic stamp mode.
            if 0 <= number <= 999:
                return number

        roman_number = re.fullmatch(
            r"[\[(\-\s.,;:]*([IVXLCDM]{1,8})[\])\-\s.,;:]*",
            stripped,
            flags=re.IGNORECASE,
        )
        if roman_number:
            value = _roman_to_int(roman_number.group(1))
            if value and 1 <= value <= 999:
                return value

        # Fallback for short footer/header lines that contain multiple numeric
        # tokens (e.g. left noise + right page number). Prefer rightmost token.
        letters = re.findall(r"[A-Za-zÄÖÜäöüß]", stripped)
        allowed_ocr_letters = {"O", "o", "D", "Q", "G", "C", "U", "I", "l"}
        if len(stripped) <= 20 and all(letter in allowed_ocr_letters for letter in letters):
            numbers = re.findall(r"\b([0-9A-Za-z!|]{1,6})\b", stripped)
            for token in reversed(numbers):
                value = _normalize_numeric_token(token)
                if value is not None:
                    return value

    return None


def _parse_page_number_priority() -> list[str]:
    """Read configurable source priority for page-number detection."""
    raw_priority = (getattr(config, "OCR_PAGE_NUMBER_PRIORITY", "book,stamp") or "book,stamp").strip()
    order = [token.strip().lower() for token in raw_priority.split(",") if token.strip()]

    normalized: list[str] = []
    for token in order:
        if token not in {"book", "stamp"}:
            continue
        if token not in normalized:
            normalized.append(token)

    if "book" not in normalized:
        normalized.append("book")
    if "stamp" not in normalized:
        normalized.append("stamp")
    return normalized


def _extract_page_number_from_pdf_text(file_relative_path: Optional[str]) -> Optional[int]:
    """Extract page number from OCR output using positional zone detection and configurable source priority."""
    image_footer = _extract_page_number_from_pdf_image_footer(file_relative_path)
    if image_footer is not None:
        return image_footer
    # Positional detection is the next-best fallback when image-based stamp OCR
    # cannot resolve a zero-padded footer stamp.
    positional = _extract_positional_page_number_from_pdf(file_relative_path)
    if positional is not None:
        return positional
    # Full-text fallback (for PDFs without readable position data).
    text = _extract_text_from_pdf_first_page(file_relative_path)
    return _extract_page_number_from_text(text)


def _extract_page_number_from_pdf_image_footer(file_relative_path: Optional[str]) -> Optional[int]:
    """Render the first page and OCR only the right footer as a last-resort stamp detector."""
    if not file_relative_path:
        return None

    fitz = getattr(pdf_ocr_module, "fitz", None)
    cv2 = getattr(pdf_ocr_module, "cv2", None)
    np = getattr(pdf_ocr_module, "np", None)
    if fitz is None or cv2 is None or np is None:
        return None

    tesseract_bin = config.get_tesseract_binary()
    if not tesseract_bin:
        return None

    pdf_path = (config.UPLOAD_DIRECTORY / file_relative_path).resolve()
    if not pdf_path.exists() or not pdf_path.is_file():
        return None

    try:
        doc = fitz.open(pdf_path)
        try:
            if doc.page_count == 0:
                return None
            page = doc[0]
            pix = page.get_pixmap(dpi=max(int(config.OCR_DPI), 300), alpha=False)
        finally:
            doc.close()

        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        height, width = gray.shape
        # Focus on the stamp area seen in the sample scans.
        crop = gray[int(height * 0.78) :, int(width * 0.58) :]
        if crop.size == 0:
            return None

        enlarged = cv2.resize(crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(enlarged, (3, 3), 0)
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        inv = cv2.bitwise_not(otsu)

        candidates = [otsu, inv]
        seen: set[int] = set()
        with tempfile.TemporaryDirectory(prefix="nlf-page-number-") as tmp_dir:
            for index, image in enumerate(candidates):
                image_path = Path(tmp_dir) / f"footer_{index}.png"
                if not cv2.imwrite(str(image_path), image):
                    continue

                cmd = [
                    tesseract_bin,
                    str(image_path),
                    "stdout",
                    "--psm",
                    "7",
                    "-c",
                    "tessedit_char_whitelist=0123456789ODQGCUIl|!",
                ]
                completed = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=30,
                )
                output = (completed.stdout or "").strip()
                value = _extract_stamp_page_number_from_text(output)
                if value is not None and value not in seen:
                    seen.add(value)
                    return value
        return None
    except Exception:
        return None


def _extract_positional_page_number_from_pdf(file_relative_path: Optional[str]) -> Optional[int]:
    """
    Detect page number using PDF text positions via pypdf visitor.
    Checks the right footer first (bottom 20 %, right 40 %), then whole footer/header.
    Returns None when zones contain no recognisable page number or on any error.
    """
    if not file_relative_path:
        return None
    pdf_path = (config.UPLOAD_DIRECTORY / file_relative_path).resolve()
    if not pdf_path.exists() or not pdf_path.is_file():
        return None
    try:
        reader = PdfReader(str(pdf_path))
        if not reader.pages:
            return None
        page = reader.pages[0]
        x_min = float(page.mediabox.lower_left[0])
        x_max = float(page.mediabox.upper_right[0])
        y_min = float(page.mediabox.lower_left[1])
        y_max = float(page.mediabox.upper_right[1])
        width = x_max - x_min
        height = y_max - y_min
        if width == 0 or height == 0:
            return None

        raw: list[tuple[str, float, float]] = []

        def visitor(text: str, cm, tm, fontdict, fontsize) -> None:
            # tm can be None when called outside a text object
            if text and text.strip() and tm is not None:
                x_norm = (float(tm[4]) - x_min) / width
                y_norm = (float(tm[5]) - y_min) / height
                raw.append((text, y_norm, x_norm))

        page.extract_text(visitor_text=visitor)

        if not raw:
            return None

        # Group fragments at nearby y-positions (within 2 % of page height) into lines.
        sorted_raw = sorted(raw, key=lambda s: (round(s[1], 4), s[2]))
        lines: list[tuple[str, float, float]] = []
        buf_chunks: list[tuple[float, str]] = [(sorted_raw[0][2], sorted_raw[0][0])]
        buf_y = sorted_raw[0][1]
        for txt, y, x in sorted_raw[1:]:
            if abs(y - buf_y) > 0.02:
                ordered = " ".join(text for _, text in sorted(buf_chunks, key=lambda c: c[0]))
                max_x = max(chunk_x for chunk_x, _ in buf_chunks)
                lines.append((ordered, buf_y, max_x))
                buf_chunks = []
                buf_y = y
            buf_chunks.append((x, txt))
        if buf_chunks:
            ordered = " ".join(text for _, text in sorted(buf_chunks, key=lambda c: c[0]))
            max_x = max(chunk_x for chunk_x, _ in buf_chunks)
            lines.append((ordered, buf_y, max_x))

        def _collapse_digit_fragments(s: str) -> str:
            """OCRmyPDF emits every digit as a separate fragment; '2 1 6' → '216'."""
            stripped = s.strip()
            # Collapse only when all tokens are single digits, not for multi-number lines.
            if re.fullmatch(r"(?:\d\s+)+\d", stripped):
                return re.sub(r"\s+", "", stripped)
            return s

        right_footer_text = "\n".join(
            _collapse_digit_fragments(t) for t, y, max_x in lines if y <= 0.20 and max_x >= 0.60
        )
        footer_text = "\n".join(_collapse_digit_fragments(t) for t, y, _ in lines if y <= 0.20)
        header_text = "\n".join(_collapse_digit_fragments(t) for t, y, _ in lines if y >= 0.85)

        for zone_text in (right_footer_text, footer_text, header_text):
            if not zone_text.strip():
                continue
            num = _extract_stamp_page_number_from_text(zone_text)
            if num is not None:
                return num
            num = _extract_book_page_number_from_text(zone_text)
            if num is not None:
                return num

        return None
    except Exception:
        return None


def _extract_page_number_from_text(text: str) -> Optional[int]:
    """Extract page number from already extracted OCR text."""
    if not text.strip():
        return None

    extractor_map = {
        "book": _extract_book_page_number_from_text,
        "stamp": _extract_stamp_page_number_from_text,
    }

    for source in _parse_page_number_priority():
        extractor = extractor_map[source]
        number = extractor(text)
        if number is not None:
            return number

    return None


def _update_page_comment_with_detected_page_number(page: Page) -> None:
    """Write standardized page-number information to pages.comment."""
    detected_number = _extract_page_number_from_pdf_text(page.current_file)
    if detected_number is None:
        page.comment = "Seite: nicht gefunden"
        return

    page.comment = f"Seite: {detected_number}"


def _populate_current_file_from_origin(db: Session, page: Page) -> None:
    """Run OCR inline or queue background OCR, then refresh page state."""
    try:
        completed_inline = PageOcrJobService.schedule_page_ocr(
            page_id=str(page.id),
            record_id=str(page.record_id) if page.record_id else None,
        )
        db.refresh(page)
        if completed_inline:
            db.refresh(page)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process OCR pipeline for uploaded PDF: {str(exc)}",
        )


@router.get("/{page_id}/download-watermarked")
async def download_watermarked_pdf(
    page_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Return a user-specific watermarked PDF for the given page."""
    page = db.query(Page).options(joinedload(Page.record)).filter(Page.id == page_id, Page.active == True).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    pdf_file = _get_preferred_pdf_file(page)
    if not pdf_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF file available for this page",
        )

    source_pdf_path = (config.UPLOAD_DIRECTORY / pdf_file).resolve()
    if not source_pdf_path.exists() or not source_pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source PDF file not found on server",
        )

    try:
        from app.services.pdf_watermark_service import create_watermarked_pdf

        watermark_bytes = create_watermarked_pdf(
            source_pdf=source_pdf_path,
            username=current_user.username,
            downloaded_at=datetime.now(),
            record_name=page.record.title if page.record else None,
            record_signature=page.record.signature if page.record else None,
            page_text=page.page,
            watermark_image_path=config.get_watermark_image_path(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate watermarked PDF: {str(exc)}",
        )

    filename_stem = Path(pdf_file).stem
    download_name = f"{filename_stem}_watermarked.pdf"

    return Response(
        content=watermark_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/{page_id}/view-pdf")
async def view_watermarked_pdf(
    page_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Return a user-specific watermarked PDF for inline viewing in the browser."""
    page = db.query(Page).options(joinedload(Page.record)).filter(Page.id == page_id, Page.active == True).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    pdf_file = _get_preferred_pdf_file(page)
    if not pdf_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF file available for this page",
        )

    source_pdf_path = (config.UPLOAD_DIRECTORY / pdf_file).resolve()
    if not source_pdf_path.exists() or not source_pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source PDF file not found on server",
        )

    try:
        from app.services.pdf_watermark_service import create_watermarked_pdf

        watermark_bytes = create_watermarked_pdf(
            source_pdf=source_pdf_path,
            username=current_user.username,
            downloaded_at=datetime.now(),
            record_name=page.record.title if page.record else None,
            record_signature=page.record.signature if page.record else None,
            page_text=page.page,
            watermark_image_path=config.get_watermark_image_path(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate watermarked PDF: {str(exc)}",
        )

    filename_stem = Path(pdf_file).stem
    view_name = f"{filename_stem}_watermarked.pdf"

    return Response(
        content=watermark_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{view_name}"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
        },
    )


@router.get("/{page_id}/thumbnail")
async def get_thumbnail_with_watermark(
    page_id: str,
    width: int = Query(200, ge=50, le=800, description="Thumbnail width in pixels"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Return a thumbnail of the first page with watermark overlay."""
    page = db.query(Page).options(joinedload(Page.record)).filter(Page.id == page_id, Page.active == True).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    pdf_file = _get_preferred_pdf_file(page)
    if not pdf_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF file available for this page",
        )

    source_pdf_path = (config.UPLOAD_DIRECTORY / pdf_file).resolve()
    if not source_pdf_path.exists() or not source_pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source PDF file not found on server",
        )

    try:
        from app.services.pdf_watermark_service import create_thumbnail_with_watermark

        thumbnail_bytes = create_thumbnail_with_watermark(
            source_pdf=source_pdf_path,
            username=current_user.username,
            downloaded_at=datetime.now(),
            record_name=page.record.title if page.record else None,
            record_signature=page.record.signature if page.record else None,
            page_text=page.page,
            watermark_image_path=config.get_watermark_image_path(),
            thumbnail_width=width,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate thumbnail with watermark: {str(exc)}",
        )

    return Response(
        content=thumbnail_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
        },
    )


@router.get("")
async def list_pages(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    record_id: Optional[str] = Query(None, description="Filter by record ID"),
    name: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List all pages with optional filters
    """
    from sqlalchemy.orm import joinedload
    
    # Base query with eager loading of relationships
    query = db.query(Page).filter(Page.active == True)
    
    # Eagerly load relationships
    query = query.options(
        joinedload(Page.record),
        joinedload(Page.restriction),
        joinedload(Page.workstatus)
    )
    
    # Filter by record_id
    if record_id:
        query = query.filter(Page.record_id == record_id)
    
    # Search by name
    if name:
        query = query.filter(Page.name.ilike(f"%{name}%"))
    
    # Get total count
    total = query.distinct().count()

    # Default sort: order_by ascending, fallback to name if null
    pages = query.order_by(Page.order_by.asc().nullslast(), Page.name.asc()).distinct().offset(skip).limit(limit).all()
    
    return {
        "items": [
            {
                "id": str(page.id),
                "name": page.name,
                "description": page.description,
                "page": page.page,
                "comment": page.comment,
                "record_id": str(page.record_id),
                "orgin_file": page.orgin_file,
                "record_title": page.record.title if page.record else None,
                "record_signature": page.record.signature if page.record else None,
                "location_file": page.location_file,
                "current_file": page.current_file,
                "ocr_status": _get_ocr_status(page),
                "restriction_file": page.restriction_file,
                "location_thumbnail": page.location_thumbnail,
                "location_file_watermark": page.location_file_watermark,
                "restriction_id": str(page.restriction_id),
                "restriction": page.restriction.name if page.restriction else None,
                "workstatus_id": str(page.workstatus_id) if page.workstatus_id else None,
                "workstatus": page.workstatus.status if page.workstatus else None,
                "created_on": page.created_on.isoformat() if page.created_on else None,
                "created_by": str(page.created_by) if page.created_by else None,
                "order_by": page.order_by,
            }
            for page in pages
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{page_id}")
async def get_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get a specific page by ID
    """
    import uuid
    page_uuid = uuid.UUID(page_id) if not isinstance(page_id, uuid.UUID) else page_id
    page = db.query(Page).filter(Page.id == page_uuid, Page.active == True).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    return {
        "id": str(page.id),
        "name": page.name,
        "description": page.description,
        "page": page.page,
        "comment": page.comment,
        "record_id": str(page.record_id),
        "orgin_file": page.orgin_file,
        "record_title": page.record.title if page.record else None,
        "record_signature": page.record.signature if page.record else None,
        "location_file": page.location_file,
        "current_file": page.current_file,
        "ocr_status": _get_ocr_status(page),
        "restriction_file": page.restriction_file,
        "location_thumbnail": page.location_thumbnail,
        "location_file_watermark": page.location_file_watermark,
        "restriction_id": str(page.restriction_id),
        "restriction": page.restriction.name if page.restriction else None,
        "workstatus_id": str(page.workstatus_id) if page.workstatus_id else None,
        "workstatus": page.workstatus.status if page.workstatus else None,
        "created_on": page.created_on.isoformat() if page.created_on else None,
        "created_by": str(page.created_by) if page.created_by else None,
        "last_modified_on": page.last_modified_on.isoformat() if page.last_modified_on else None,
        "last_modified_by": str(page.last_modified_by) if page.last_modified_by else None,
        "order_by": page.order_by,
    }


@router.post("")
async def create_page(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    page: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    record_id: str = Form(...),
    restriction_id: str = Form(...),
    workstatus_id: Optional[str] = Form(None),
    order_by: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Create a new page with optional file upload
    Only users with 'admin' or 'user_scan' role can create pages
    """
    # Rollen-Prüfung
    if not (current_user.has_role("admin") or current_user.has_role("user_scan")):
        raise HTTPException(status_code=403, detail="Not authorized to create pages")

    import uuid
    # Konvertiere IDs zu UUID-Objekten
    record_uuid = uuid.UUID(record_id) if not isinstance(record_id, uuid.UUID) else record_id
    restriction_uuid = uuid.UUID(restriction_id) if not isinstance(restriction_id, uuid.UUID) else restriction_id
    user_uuid = uuid.UUID(str(current_user.id)) if not isinstance(current_user.id, uuid.UUID) else current_user.id
    workstatus_uuid = uuid.UUID(workstatus_id) if workstatus_id else None

    location_file = None
    split_pdf = False
    created_count = 1
    location_files = []
    pdf_bytes = None
    record_signature = None
    # Hole die Signatur für den Speicherpfad
    record = db.query(Record).filter(Record.id == record_uuid).first()
    if record:
        record_signature = record.signature
    if file:
        validate_file(file)
        pdf_bytes = file.file.read()
        file.file.seek(0)
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            if reader.is_encrypted:
                raise HTTPException(status_code=400, detail="Invalid PDF file: Encrypted PDF files are not supported")
            num_pages = len(reader.pages)
            from app.services.page_service import PageService
            from pypdf import PdfWriter
            from app.routes import pages as pages_routes
            import shutil
            if num_pages > 1:
                split_pdf = True
                created_count = num_pages
                # Bestimme Startwert für order_by (höchster Wert + 1)
                max_order = db.query(Page).filter(Page.record_id == record_uuid).order_by(Page.order_by.desc()).with_entities(Page.order_by).first()
                start_order = (max_order[0] if max_order and max_order[0] is not None else 0) + 1
                new_pages = []
                for i in range(num_pages):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    buffer = BytesIO()
                    writer.write(buffer)
                    single_pdf_bytes = buffer.getvalue()
                    # Always use 'Seite_{i+1}.pdf' for split pages
                    filename = f"Seite_{i+1}.pdf"
                    rel_path = _save_pdf_content(single_pdf_bytes, record_signature, str(record_uuid), filename, storage_subdir="origin")
                    # Always copy file to current folder as Seite_{i+1}_current.pdf
                    signature_folder = _build_signature_folder_name(record_signature, str(record_uuid))
                    current_filename = f"Seite_{i+1}_current.pdf"
                    current_rel_path = f"{signature_folder}/current/{current_filename}"
                    origin_abs = config.UPLOAD_DIRECTORY / rel_path
                    current_abs = config.UPLOAD_DIRECTORY / current_rel_path
                    current_abs.parent.mkdir(parents=True, exist_ok=True)
                    with open(current_abs, "wb") as f_out:
                        f_out.write(single_pdf_bytes)
                    # Kommentar für jede Seite bestimmen
                    text = reader.pages[i].extract_text() or ""
                    page_number = None
                    if hasattr(pages_routes, "_extract_page_number_from_pdf_text"):
                        page_number = pages_routes._extract_page_number_from_pdf_text(text)
                    if page_number is not None:
                        page_comment = f"Seite: {page_number}"
                    else:
                        page_comment = "Seite: nicht gefunden"
                    # Setze order_by für jede neue Seite
                    this_order = start_order + i
                    new_page = PageService.create_page(
                        db=db,
                        name=f"Seite {i+1}",
                        record_id=record_uuid,
                        restriction_id=restriction_uuid,
                        user_id=user_uuid,
                        description=description,
                        page=page,
                        comment=page_comment,
                        location_file=rel_path,
                        workstatus_id=workstatus_uuid,
                        order_by=this_order,
                    )
                    db.flush()
                    db.refresh(new_page)
                    # Ensure current_file is set to current_rel_path if OCR disabled
                    if getattr(config, "OCR_PIPELINE_ENABLED", True) is False:
                        new_page.current_file = current_rel_path
                        db.flush()
                    new_pages.append(new_page)
                db.commit()
                # OCR-Job für jede neue Seite erst nach Commit starten
                for new_page in new_pages:
                    try:
                        _populate_current_file_from_origin(db, new_page)
                    except Exception as ocr_exc:
                        logger.warning(f"OCR-Job konnte für Page {new_page.id} nicht gestartet werden: {ocr_exc}")
                # Build items list for response
                items = []
                ocr_enabled = getattr(config, "OCR_PIPELINE_ENABLED", True)
                ocr_async = getattr(config, "OCR_PIPELINE_ASYNC", False)
                for i, p in enumerate(new_pages):
                    signature_folder = _build_signature_folder_name(record_signature, str(record_uuid))
                    current_filename = f"Seite_{i+1}_current.pdf"
                    current_rel_path = f"{signature_folder}/current/{current_filename}"
                    items.append({
                        "id": str(p.id),
                        "name": p.name,
                        "description": p.description,
                        "page": p.page,
                        "comment": p.comment,
                        "record_id": str(p.record_id),
                        "location_file": p.location_file,
                        "current_file": None if (ocr_enabled and ocr_async) else current_rel_path,
                        "restriction_id": str(p.restriction_id),
                        "workstatus_id": str(p.workstatus_id) if p.workstatus_id else None,
                        "created_on": p.created_on.isoformat() if p.created_on else None,
                        "created_by": str(p.created_by) if p.created_by else None,
                        "last_modified_on": p.last_modified_on.isoformat() if p.last_modified_on else None,
                        "last_modified_by": str(p.last_modified_by) if p.last_modified_by else None,
                        "order_by": p.order_by,
                        "ocr_status": "pending",
                    })
                return {
                    "items": items,
                    "split_pdf": True,
                    "created_count": created_count,
                }
            else:
                # Always use 'Seite_{timestamp}.pdf' for single-page
                filename = f"Seite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                location_file = _save_pdf_content(pdf_bytes, record_signature, str(record_uuid), filename, storage_subdir="origin")
                # Compute current_file path
                signature_folder = _build_signature_folder_name(record_signature, str(record_uuid))
                current_filename = filename.replace('.pdf', '_current.pdf')
                current_rel_path = f"{signature_folder}/current/{current_filename}"
                if getattr(config, "OCR_PIPELINE_ENABLED", True) is False:
                    origin_abs = config.UPLOAD_DIRECTORY / location_file
                    current_abs = config.UPLOAD_DIRECTORY / current_rel_path
                    current_abs.parent.mkdir(parents=True, exist_ok=True)
                    with open(current_abs, "wb") as f_out:
                        f_out.write(pdf_bytes)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid PDF file: {str(exc)}")

    from app.services.page_service import PageService
    # Kommentar immer automatisch setzen, wenn PDF vorhanden
    final_comment = comment
    if file and pdf_bytes is not None:
        from app.routes import pages as pages_routes
        text = ""
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            if reader.pages:
                text = reader.pages[0].extract_text() or ""
        except Exception:
            pass
        page_number = None
        if hasattr(pages_routes, "_extract_page_number_from_pdf_text"):
            page_number = pages_routes._extract_page_number_from_pdf_text(text)
        if page_number is not None:
            final_comment = f"Seite: {page_number}"
        else:
            final_comment = "Seite: nicht gefunden"

    new_page = PageService.create_page(
        db=db,
        name=name,
        record_id=record_uuid,
        restriction_id=restriction_uuid,
        user_id=user_uuid,
        description=description,
        page=page,
        comment=final_comment,
        location_file=location_file,
        workstatus_id=workstatus_uuid,
        order_by=order_by,
    )
    db.commit()
    db.refresh(new_page)
    # Ensure current_file is set to current_rel_path if OCR disabled
    if getattr(config, "OCR_PIPELINE_ENABLED", True) is False and file and pdf_bytes is not None:
        signature_folder = _build_signature_folder_name(record_signature, str(record_uuid))
        filename = location_file.split("/")[-1]
        current_filename = filename.replace('.pdf', '_current.pdf')
        current_rel_path = f"{signature_folder}/current/{current_filename}"
        new_page.current_file = current_rel_path
        db.flush()
    db.refresh(new_page)

    # Compute expected current_file path for single-page
    signature_folder = _build_signature_folder_name(record_signature, str(record_uuid))
    filename = location_file.split("/")[-1] if location_file else ""
    current_filename = filename.replace('.pdf', '_current.pdf') if filename else ""
    current_rel_path = f"{signature_folder}/current/{current_filename}" if filename else None
    ocr_enabled = getattr(config, "OCR_PIPELINE_ENABLED", True)
    ocr_async = getattr(config, "OCR_PIPELINE_ASYNC", False)
    return {
        "id": str(new_page.id),
        "name": new_page.name,
        "description": new_page.description,
        "page": new_page.page,
        "comment": new_page.comment,
        "record_id": str(new_page.record_id),
        "location_file": new_page.location_file,
        "current_file": None if (ocr_enabled and ocr_async) else current_rel_path,
        "restriction_id": str(new_page.restriction_id),
        "workstatus_id": str(new_page.workstatus_id) if new_page.workstatus_id else None,
        "created_on": new_page.created_on.isoformat() if new_page.created_on else None,
        "created_by": str(new_page.created_by) if new_page.created_by else None,
        "last_modified_on": new_page.last_modified_on.isoformat() if new_page.last_modified_on else None,
        "last_modified_by": str(new_page.last_modified_by) if new_page.last_modified_by else None,
        "order_by": new_page.order_by,
        "ocr_status": "pending",
        "split_pdf": split_pdf,
        "created_count": created_count,
    }


@router.put("/{page_id}")
async def update_page(
    page_id: str,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    page: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    restriction_id: str = Form(...),
    workstatus_id: Optional[str] = Form(None),
    order_by: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    delete_file: Optional[bool] = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update an existing page
    Only users with 'admin' or 'user_page' role can update pages
    """
    can_edit_page = current_user.has_role("admin") or current_user.has_role("user_page")
    can_manage_file = current_user.has_role("admin") or current_user.has_role("user_scan")

    # User must be allowed to either edit page data or manage files.
    if not (can_edit_page or can_manage_file):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only admin, user_page, or user_scan can update pages."
        )

    page_uuid = _parse_uuid(page_id, "page_id")
    restriction_uuid = _parse_uuid(restriction_id, "restriction_id")
    workstatus_uuid = _parse_uuid(workstatus_id, "workstatus_id") if workstatus_id else None

    # Get existing page
    existing_page = db.query(Page).filter(Page.id == page_uuid, Page.active == True).first()
    
    if not existing_page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Validate that restriction exists
    restriction = db.query(Restriction).filter(Restriction.id == restriction_uuid).first()
    if not restriction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restriction not found"
        )
    
    # Validate that workstatus exists (if provided)
    if workstatus_uuid:
        workstatus = db.query(WorkStatus).filter(WorkStatus.id == workstatus_uuid).first()
        if not workstatus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="WorkStatus not found"
            )
    
    # Update non-file fields only for users with page edit permissions.
    if can_edit_page:
        existing_page.name = name
        existing_page.description = description
        existing_page.page = page
        existing_page.comment = comment
        existing_page.restriction_id = restriction_uuid
        existing_page.workstatus_id = workstatus_uuid
        existing_page.last_modified_by = current_user.id
        existing_page.last_modified_on = datetime.now(timezone.utc)
        if order_by is not None:
            try:
                existing_page.order_by = int(order_by)
            except Exception:
                pass
    
    # Handle file deletion
    if delete_file and existing_page.location_file:
        if not can_manage_file:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to remove files."
            )
        delete_uploaded_file(existing_page.location_file)
        existing_page.location_file = None
        if existing_page.current_file:
            delete_uploaded_file(existing_page.current_file)
            existing_page.current_file = None
    
    # Handle file upload (replaces existing file)
    if file and file.filename:
        if not can_manage_file:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to upload files."
            )
        validate_file(file)
        pdf_content = file.file.read()
        if len(pdf_content) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {config.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )
        _check_single_page_pdf(pdf_content)
        # Delete old file if exists
        if existing_page.location_file:
            delete_uploaded_file(existing_page.location_file)
        # Save new file
        filename = f"Seite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        location_file = _save_pdf_content(
            pdf_content,
            existing_page.record.signature if existing_page.record else None,
            str(existing_page.record_id),
            filename,
            storage_subdir="origin",
        )
        existing_page.location_file = location_file
    db.commit()
    if file and file.filename:
        db.refresh(existing_page)
        _populate_current_file_from_origin(db, existing_page)
    db.refresh(existing_page)
    
    return {
        "id": str(existing_page.id),
        "name": existing_page.name,
        "description": existing_page.description,
        "page": existing_page.page,
        "comment": existing_page.comment,
        "record_id": str(existing_page.record_id),
        "orgin_file": existing_page.orgin_file,
        "location_file": existing_page.location_file,
        "current_file": existing_page.current_file,
        "ocr_status": _get_ocr_status(existing_page),
        "restriction_file": existing_page.restriction_file,
        "restriction_id": str(existing_page.restriction_id),
        "workstatus_id": str(existing_page.workstatus_id) if existing_page.workstatus_id else None,
        "last_modified_on": existing_page.last_modified_on.isoformat() if existing_page.last_modified_on else None,
    }


@router.delete("/{page_id}")
async def delete_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Soft delete a page (set active=False)
    """
    page = db.query(Page).filter(Page.id == page_id, Page.active == True).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Soft delete
    if page.location_file:
        delete_uploaded_file(page.location_file)
    if page.current_file:
        delete_uploaded_file(page.current_file)

    page.active = False
    page.last_modified_by = current_user.id
    page.last_modified_on = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"message": "Page deleted successfully"}
