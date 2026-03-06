"""PDF watermark generation utilities."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pdf2image import convert_from_path
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

    if watermark_image_path and watermark_image_path.exists() and watermark_image_path.is_file():
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
    else:
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
    """Generate a thumbnail of the first page with watermark overlay."""
    try:
        # Convert first page to image with 150 DPI for good quality
        images = convert_from_path(
            str(source_pdf),
            first_page=1,
            last_page=1,
            dpi=150,
        )
        
        if not images:
            raise ValueError("Could not convert PDF to image")
        
        # Get first page
        pdf_image = images[0]
        
        # Calculate thumbnail size maintaining aspect ratio
        aspect_ratio = pdf_image.height / pdf_image.width
        thumbnail_height = int(thumbnail_width * aspect_ratio)
        
        # Resize image
        thumbnail = pdf_image.resize(
            (thumbnail_width, thumbnail_height),
            Image.Resampling.LANCZOS
        )
        
        # Create watermark overlay
        overlay = Image.new("RGBA", thumbnail.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Scale factors for positioning
        scale_x = thumbnail_width / 595.0  # A4 width in points
        scale_y = thumbnail_height / 842.0  # A4 height in points
        
        # Diagonal "CONFIDENTIAL" label
        font_size = max(12, int(min(thumbnail_width, thumbnail_height) * 0.08))
        try:
            # Try to use a bold font
            font_bold = ImageFont.truetype("arialbd.ttf", font_size)
            font_regular = ImageFont.truetype("arial.ttf", max(7, int(font_size * 0.5)))
            font_small = ImageFont.truetype("arial.ttf", max(6, int(font_size * 0.4)))
        except:
            # Fallback to default font
            font_bold = ImageFont.load_default()
            font_regular = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw diagonal CONFIDENTIAL
        center_x = thumbnail_width // 2
        center_y = thumbnail_height // 2
        
        # Create a temporary image for rotation
        diagonal_text = "CONFIDENTIAL"
        text_bbox = draw.textbbox((0, 0), diagonal_text, font=font_bold)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Create text image
        text_image = Image.new("RGBA", (text_width + 20, text_height + 20), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_image)
        text_draw.text(
            (10, 10),
            diagonal_text,
            fill=(217, 13, 13, 36),  # Red with transparency
            font=font_bold
        )
        
        # Rotate text
        rotated_text = text_image.rotate(38, expand=True)
        
        # Paste rotated text at center
        paste_x = center_x - rotated_text.width // 2
        paste_y = center_y - rotated_text.height // 2
        overlay.paste(rotated_text, (paste_x, paste_y), rotated_text)
        
        # Header badge area
        left_x = int(36 * scale_x)
        top_y = int(36 * scale_y)
        
        # Optional watermark image
        if watermark_image_path and watermark_image_path.exists() and watermark_image_path.is_file():
            try:
                logo = Image.open(watermark_image_path)
                logo_height = int(40 * scale_y)
                logo_width = int(logo.width * (logo_height / logo.height))
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                
                # Convert to RGBA if needed
                if logo.mode != "RGBA":
                    logo = logo.convert("RGBA")
                
                overlay.paste(logo, (left_x, top_y), logo)
                text_start_x = left_x + logo_width + int(10 * scale_x)
            except:
                text_start_x = left_x
        else:
            text_start_x = left_x
        
        # Draw header text
        y_pos = top_y
        draw.text((text_start_x, y_pos), "CONFIDENTIAL", fill=(26, 26, 26, 230), font=font_regular)
        
        y_pos += int(12 * scale_y)
        username_short = _fit_text(username, 25)
        draw.text((text_start_x, y_pos), f"Downloaded by: {username_short}", fill=(26, 26, 26, 230), font=font_small)
        
        y_pos += int(10 * scale_y)
        draw.text((text_start_x, y_pos), downloaded_at.strftime("%Y-%m-%d %H:%M"), fill=(26, 26, 26, 230), font=font_small)
        
        # Record info (right-aligned)
        right_x = thumbnail_width - int(36 * scale_x)
        info_y = top_y + int(38 * scale_y)
        
        info_lines = [
            f"Record: {_fit_text(record_name, 20)}",
            f"Sign: {_fit_text(record_signature, 15)}",
            f"Page: {_fit_text(page_text, 15)}",
        ]
        
        for line in info_lines:
            bbox = draw.textbbox((0, 0), line, font=font_small)
            line_width = bbox[2] - bbox[0]
            draw.text((right_x - line_width, info_y), line, fill=(26, 26, 26, 230), font=font_small)
            info_y += int(9 * scale_y)
        
        # Composite thumbnail with watermark
        if thumbnail.mode != "RGBA":
            thumbnail = thumbnail.convert("RGBA")
        
        watermarked = Image.alpha_composite(thumbnail, overlay)
        
        # Convert to RGB for JPEG output
        watermarked_rgb = watermarked.convert("RGB")
        
        # Save to bytes
        output = BytesIO()
        watermarked_rgb.save(output, format="JPEG", quality=85, optimize=True)
        output.seek(0)
        
        return output.read()
        
    except Exception as e:
        raise RuntimeError(f"Failed to create thumbnail with watermark: {str(e)}")
