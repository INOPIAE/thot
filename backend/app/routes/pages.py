"""
Pages API routes
"""

from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.page import Page
from app.models.record import Record
from app.models.restriction import Restriction
from app.models.workstatus import WorkStatus
from app.utils.auth import get_current_user
from config import config

router = APIRouter(prefix="/pages", tags=["pages"])

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


def save_uploaded_file(file: UploadFile, record_signature: Optional[str], record_id: str) -> str:
    """Save uploaded file to disk and return relative path"""
    # Create directory structure: uploads/{signature_folder}/
    signature_folder = _build_signature_folder_name(record_signature, record_id)
    record_dir = config.UPLOAD_DIRECTORY / signature_folder
    record_dir.mkdir(parents=True, exist_ok=True)
    
    # Store uploaded PDFs with fixed naming convention.
    filename = f"Seite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = record_dir / filename
    
    # Save file
    with open(file_path, "wb") as f:
        content = file.file.read()
        # Check file size
        if len(content) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {config.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )
        f.write(content)
    
    # Return relative path for database storage
    return f"{signature_folder}/{filename}"


def delete_uploaded_file(location_file: str) -> None:
    """Delete file from disk"""
    if location_file:
        file_path = config.UPLOAD_DIRECTORY / location_file
        if file_path.exists():
            file_path.unlink()


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

    if not page.location_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF file available for this page",
        )

    source_pdf_path = (config.UPLOAD_DIRECTORY / page.location_file).resolve()
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

    filename_stem = Path(page.location_file).stem
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

    if not page.location_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF file available for this page",
        )

    source_pdf_path = (config.UPLOAD_DIRECTORY / page.location_file).resolve()
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

    filename_stem = Path(page.location_file).stem
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

    if not page.location_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF file available for this page",
        )

    source_pdf_path = (config.UPLOAD_DIRECTORY / page.location_file).resolve()
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
    
    # Get paginated results
    pages = query.distinct().offset(skip).limit(limit).all()
    
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
                "restriction_file": page.restriction_file,
                "location_thumbnail": page.location_thumbnail,
                "location_file_watermark": page.location_file_watermark,
                "restriction_id": str(page.restriction_id),
                "restriction": page.restriction.name if page.restriction else None,
                "workstatus_id": str(page.workstatus_id) if page.workstatus_id else None,
                "workstatus": page.workstatus.status if page.workstatus else None,
                "created_on": page.created_on.isoformat() if page.created_on else None,
                "created_by": str(page.created_by) if page.created_by else None,
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
    page = db.query(Page).filter(Page.id == page_id, Page.active == True).first()
    
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
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Create a new page with optional file upload
    Only users with 'admin' or 'user_scan' role can create pages
        # Check user permissions
        if not (current_user.has_role("admin") or current_user.has_role("user_scan")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Only admin or user_scan can create pages."
            )
    
    """
    # Validate that record exists
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    
    # Validate that restriction exists
    restriction = db.query(Restriction).filter(Restriction.id == restriction_id).first()
    if not restriction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restriction not found"
        )
    
    # Validate that workstatus exists (if provided)
    if workstatus_id:
        workstatus = db.query(WorkStatus).filter(WorkStatus.id == workstatus_id).first()
        if not workstatus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="WorkStatus not found"
            )
    
    # Create page object
    new_page = Page(
        name=name,
        description=description,
        page=page,
        comment=comment,
        record_id=record_id,
        restriction_id=restriction_id,
        workstatus_id=workstatus_id,
        created_by=current_user.id,
        last_modified_by=current_user.id,
    )
    
    db.add(new_page)
    db.flush()  # Get the page ID
    
    # Handle file upload if provided
    if file and file.filename:
        validate_file(file)
        location_file = save_uploaded_file(file, record.signature, str(record.id))
        new_page.location_file = location_file
    
    db.commit()
    db.refresh(new_page)
    
    return {
        "id": str(new_page.id),
        "name": new_page.name,
        "description": new_page.description,
        "page": new_page.page,
        "comment": new_page.comment,
        "record_id": str(new_page.record_id),
        "orgin_file": new_page.orgin_file,
        "location_file": new_page.location_file,
        "current_file": new_page.current_file,
        "restriction_file": new_page.restriction_file,
        "restriction_id": str(new_page.restriction_id),
        "workstatus_id": str(new_page.workstatus_id) if new_page.workstatus_id else None,
        "created_on": new_page.created_on.isoformat() if new_page.created_on else None,
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
    file: Optional[UploadFile] = File(None),
    delete_file: Optional[bool] = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update an existing page
    Only users with 'admin' or 'user_page' role can update pages
        can_edit_page = current_user.has_role("admin") or current_user.has_role("user_page")
        can_manage_file = current_user.has_role("admin") or current_user.has_role("user_scan")

        # User must be allowed to either edit page data or manage files.
        if not (can_edit_page or can_manage_file):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Only admin, user_page, or user_scan can update pages."
            )
    
    """
    # Get existing page
    existing_page = db.query(Page).filter(Page.id == page_id, Page.active == True).first()
    
    if not existing_page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Validate that restriction exists
    restriction = db.query(Restriction).filter(Restriction.id == restriction_id).first()
    if not restriction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restriction not found"
        )
    
    # Validate that workstatus exists (if provided)
    if workstatus_id:
        workstatus = db.query(WorkStatus).filter(WorkStatus.id == workstatus_id).first()
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
        existing_page.restriction_id = restriction_id
        existing_page.workstatus_id = workstatus_id
        existing_page.last_modified_by = current_user.id
        existing_page.last_modified_on = datetime.now(timezone.utc)
    
    # Handle file deletion
    if delete_file and existing_page.location_file:
        if not can_manage_file:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to remove files."
            )
        delete_uploaded_file(existing_page.location_file)
        existing_page.location_file = None
    
    # Handle file upload (replaces existing file)
    if file and file.filename:
        if not can_manage_file:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to upload files."
            )
        validate_file(file)
        # Delete old file if exists
        if existing_page.location_file:
            delete_uploaded_file(existing_page.location_file)
        # Save new file
        location_file = save_uploaded_file(
            file,
            existing_page.record.signature if existing_page.record else None,
            str(existing_page.record_id),
        )
        existing_page.location_file = location_file
    
    db.commit()
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
    page.active = False
    page.last_modified_by = current_user.id
    page.last_modified_on = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"message": "Page deleted successfully"}
