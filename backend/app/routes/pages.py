"""
Pages API routes
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

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


def save_uploaded_file(file: UploadFile, record_id: str, page_id: str) -> str:
    """Save uploaded file to disk and return relative path"""
    # Create directory structure: uploads/{record_id}/
    record_dir = config.UPLOAD_DIRECTORY / str(record_id)
    record_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename with original extension
    file_ext = Path(file.filename).suffix
    filename = f"{page_id}{file_ext}"
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
    return f"{record_id}/{filename}"


def delete_uploaded_file(location_file: str) -> None:
    """Delete file from disk"""
    if location_file:
        file_path = config.UPLOAD_DIRECTORY / location_file
        if file_path.exists():
            file_path.unlink()


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
                "record_title": page.record.title if page.record else None,
                "record_signature": page.record.signature if page.record else None,
                "location_file": page.location_file,
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
        "record_title": page.record.title if page.record else None,
        "record_signature": page.record.signature if page.record else None,
        "location_file": page.location_file,
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
        location_file = save_uploaded_file(file, record_id, str(new_page.id))
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
        "location_file": new_page.location_file,
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
    
    # Update fields
    existing_page.name = name
    existing_page.description = description
    existing_page.page = page
    existing_page.comment = comment
    existing_page.restriction_id = restriction_id
    existing_page.workstatus_id = workstatus_id
    existing_page.last_modified_by = current_user.id
    existing_page.last_modified_on = datetime.utcnow()
    
    # Handle file deletion
    if delete_file and existing_page.location_file:
        delete_uploaded_file(existing_page.location_file)
        existing_page.location_file = None
    
    # Handle file upload (replaces existing file)
    if file and file.filename:
        validate_file(file)
        # Delete old file if exists
        if existing_page.location_file:
            delete_uploaded_file(existing_page.location_file)
        # Save new file
        location_file = save_uploaded_file(file, str(existing_page.record_id), page_id)
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
        "location_file": existing_page.location_file,
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
    page.last_modified_on = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Page deleted successfully"}
