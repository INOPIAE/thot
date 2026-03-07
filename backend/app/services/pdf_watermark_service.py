"""PDF watermark generation utilities."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont


def _fit_text(value: Optional[str], max_len: int = 110) -> str:
    """Keep watermark lines compact to avoid layout overflow."""
    text = (value or "").strip()
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def _build_overlay_page(
    width: float,
    height: float,
    username: str,
    downloaded_at: datetime,
    record_name: Optional[str],
    record_signature: Optional[str],
    page_text: Optional[str],
    watermark_image_path: Optional[Path],
) -> bytes:
    """Create one transparent overlay page matching the PDF page size."""
    buffer = BytesIO()
    overlay = canvas.Canvas(buffer, pagesize=(width, height))

    # Diagonal background label.
    overlay.saveState()
    overlay.translate(width / 2, height / 2)
    overlay.rotate(38)
    overlay.setFillColor(Color(0.85, 0.05, 0.05, alpha=0.14))
    overlay.setFont("Helvetica-Bold", min(width, height) * 0.12)
    overlay.drawCentredString(0, 0, "CONFIDENTIAL")
    overlay.restoreState()

    # Header badge area with optional image.
    left_x = 36
    right_x = width - 36
    top_y = height - 36

    text_start_x = left_x
    if watermark_image_path and watermark_image_path.exists() and watermark_image_path.is_file():
        try:
            image_reader = ImageReader(str(watermark_image_path))
            img_width, img_height = image_reader.getSize()
            target_height = 58
            scale = target_height / max(img_height, 1)
            target_width = max(32, img_width * scale)
            overlay.drawImage(
                image_reader,
                left_x,
                top_y - target_height,
                width=target_width,
                height=target_height,
                preserveAspectRatio=True,
                mask="auto",
            )
            text_start_x = left_x + target_width + 14
        except Exception:
            # Do not fail watermark generation when logo loading is broken.
            text_start_x = left_x

    overlay.setFillColor(Color(0.1, 0.1, 0.1, alpha=0.9))
    overlay.setFont("Helvetica-Bold", 14)
    overlay.drawString(text_start_x, top_y, "CONFIDENTIAL")

    overlay.setFont("Helvetica", 10)
    overlay.drawString(text_start_x, top_y - 16, f"Downloaded by: {_fit_text(username, 48)}")
    overlay.drawString(text_start_x, top_y - 30, downloaded_at.strftime("%Y-%m-%d %H:%M"))

    # Record and page context block (requested metadata).
    info_lines = [
        f"Record name: {_fit_text(record_name)}",
        f"Record signature: {_fit_text(record_signature, 64)}",
        f"Page: {_fit_text(page_text)}",
    ]
    overlay.setFont("Helvetica", 9)
    line_y = top_y - 52
    for line in info_lines:
        overlay.drawRightString(right_x, line_y, line)
        line_y -= 12

    overlay.save()
    buffer.seek(0)
    return buffer.read()


def create_watermarked_pdf(
    source_pdf: Path,
    username: str,
    downloaded_at: datetime,
    record_name: Optional[str],
    record_signature: Optional[str],
    page_text: Optional[str],
    watermark_image_path: Optional[Path] = None,
) -> bytes:
    """Generate a watermarked PDF and return its binary content."""
    reader = PdfReader(str(source_pdf))
    writer = PdfWriter()

    for original_page in reader.pages:
        page_width = float(original_page.mediabox.width)
        page_height = float(original_page.mediabox.height)

        overlay_pdf_bytes = _build_overlay_page(
            width=page_width,
            height=page_height,
            username=username,
            downloaded_at=downloaded_at,
            record_name=record_name,
            record_signature=record_signature,
            page_text=page_text,
            watermark_image_path=watermark_image_path,
        )
        overlay_reader = PdfReader(BytesIO(overlay_pdf_bytes))
        original_page.merge_page(overlay_reader.pages[0])
        writer.add_page(original_page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


def create_thumbnail_with_watermark(
    source_pdf: Path,
    username: str,
    downloaded_at: datetime,
    record_name: Optional[str],
    record_signature: Optional[str],
    page_text: Optional[str],
    watermark_image_path: Optional[Path] = None,
    thumbnail_width: int = 200,
) -> bytes:
    """Generate a thumbnail of the first page with watermark overlay using PyMuPDF."""
    try:
        # Open PDF with fitz
        pdf_doc = fitz.open(str(source_pdf))
        
        if len(pdf_doc) == 0:
            raise ValueError("PDF has no pages")
        
        # Get first page
        page = pdf_doc[0]
        
        # Calculate zoom level based on desired width
        # Standard A4 width is ~595 points
        zoom = thumbnail_width / 595.0
        
        # Render page to image at specified zoom
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom * 1.5, zoom * 1.5), alpha=False)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        pdf_image = Image.open(BytesIO(img_data))
        pdf_image = pdf_image.convert("RGB")
        
        # Create watermark overlay
        overlay = Image.new("RGBA", pdf_image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Scale factors for text positioning
        actual_width = pdf_image.width
        actual_height = pdf_image.height
        scale_x = actual_width / 595.0
        scale_y = actual_height / 842.0
        
        # Diagonal "CONFIDENTIAL" label
        font_size = max(10, int(min(actual_width, actual_height) * 0.06))
        try:
            font_bold = ImageFont.truetype("arialbd.ttf", font_size)
            font_regular = ImageFont.truetype("arial.ttf", max(6, int(font_size * 0.5)))
            font_small = ImageFont.truetype("arial.ttf", max(5, int(font_size * 0.4)))
        except:
            font_bold = ImageFont.load_default()
            font_regular = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw diagonal CONFIDENTIAL
        center_x = actual_width // 2
        center_y = actual_height // 2
        
        diagonal_text = "CONFIDENTIAL"
        text_bbox = draw.textbbox((0, 0), diagonal_text, font=font_bold)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Create text image for rotation
        text_image = Image.new("RGBA", (text_width + 10, text_height + 10), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)
        text_draw.text((5, 5), diagonal_text, fill=(217, 13, 13, 40), font=font_bold)
        
        # Rotate text
        rotated_text = text_image.rotate(38, expand=True)
        paste_x = center_x - rotated_text.width // 2
        paste_y = center_y - rotated_text.height // 2
        overlay.paste(rotated_text, (paste_x, paste_y), rotated_text)
        
        # Header badge area
        left_x = int(20 * scale_x)
        top_y = int(20 * scale_y)
        
        # Optional logo
        if watermark_image_path and watermark_image_path.exists() and watermark_image_path.is_file():
            try:
                logo = Image.open(watermark_image_path)
                logo_height = int(25 * scale_y)
                logo_width = int(logo.width * (logo_height / max(logo.height, 1)))
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                
                if logo.mode != "RGBA":
                    logo = logo.convert("RGBA")
                
                overlay.paste(logo, (left_x, top_y), logo)
                text_start_x = left_x + logo_width + int(8 * scale_x)
            except:
                text_start_x = left_x
        else:
            text_start_x = left_x
        
        # Draw metadata text
        y_pos = top_y
        draw.text((text_start_x, y_pos), "CONFIDENTIAL", fill=(26, 26, 26, 230), font=font_regular)
        
        y_pos += int(10 * scale_y)
        username_short = _fit_text(username, 20)
        draw.text((text_start_x, y_pos), f"By: {username_short}", fill=(26, 26, 26, 200), font=font_small)
        
        y_pos += int(8 * scale_y)
        draw.text((text_start_x, y_pos), downloaded_at.strftime("%Y-%m-%d %H:%M"), fill=(26, 26, 26, 200), font=font_small)
        
        # Composite watermark onto image
        if pdf_image.mode != "RGBA":
            pdf_image = pdf_image.convert("RGBA")
        
        watermarked = Image.alpha_composite(pdf_image, overlay)
        
        # Convert to RGB for JPEG
        watermarked_rgb = watermarked.convert("RGB")
        
        # Save to JPEG
        output = BytesIO()
        watermarked_rgb.save(output, format="JPEG", quality=80, optimize=True)
        output.seek(0)
        
        pdf_doc.close()
        return output.read()
        
    except Exception as e:
        raise RuntimeError(f"Failed to create thumbnail with watermark: {str(e)}")
