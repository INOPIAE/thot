"""
Page service for handling page operations and file management
"""

import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Page, Record
from config import config


class PageService:
    """Service for page operations"""

    @staticmethod
    def get_upload_dir() -> Path:
        """Get or create upload directory"""
        upload_dir = config.UPLOAD_DIRECTORY
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @staticmethod
    def get_record_upload_dir(record_id: str) -> Path:
        """Get or create directory for a specific record"""
        record_dir = PageService.get_upload_dir() / str(record_id)
        record_dir.mkdir(parents=True, exist_ok=True)
        return record_dir

    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file
            
        Returns:
            True if valid, raises HTTPException otherwise
        """
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
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(config.ALLOWED_FILE_EXTENSIONS)}"
            )

        return True

    @staticmethod
    async def save_file(file: UploadFile, record_id: str) -> str:
        """
        Save uploaded file to filesystem
        
        Args:
            file: Uploaded file
            record_id: Record ID for organizing files
            
        Returns:
            Path to saved file relative to upload directory
        """
        PageService.validate_file(file)
        
        # Get record directory
        record_dir = PageService.get_record_upload_dir(record_id)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_name = f"{uuid.uuid4()}{file_ext}"
        file_path = record_dir / unique_name
        
        # Save file
        try:
            content = await file.read()
            
            # Check file size
            if len(content) > config.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {config.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
                )
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Return relative path
            relative_path = str(file_path.relative_to(config.UPLOAD_DIRECTORY))
            # Normalize path separators to forward slashes for consistency
            relative_path = relative_path.replace("\\", "/")
            
            return relative_path
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    @staticmethod
    def delete_file(location_file: str) -> bool:
        """
        Delete a file from filesystem
        
        Args:
            location_file: Relative path to file
            
        Returns:
            True if successful
        """
        if not location_file:
            return True
        
        try:
            file_path = config.UPLOAD_DIRECTORY / location_file
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            # Log error but don't raise - file may already be deleted
            import logging
            logging.warning(f"Failed to delete file {location_file}: {str(e)}")
            return False

    @staticmethod
    def get_page(db: Session, page_id: str) -> Page:
        """Get page by ID"""
        return db.query(Page).filter(Page.id == page_id, Page.active == True).first()

    @staticmethod
    def get_pages_for_record(db: Session, record_id: str) -> list:
        """Get all active pages for a record"""
        return db.query(Page).filter(
            and_(
                Page.record_id == record_id,
                Page.active == True
            )
        ).all()

    @staticmethod
    def create_page(
        db: Session,
        name: str,
        record_id: str,
        restriction_id: str,
        user_id: str,
        description: str = None,
        page: str = None,
        comment: str = None,
        location_file: str = None,
    ) -> Page:
        """Create a new page"""
        new_page = Page(
            name=name,
            description=description,
            page=page,
            comment=comment,
            record_id=record_id,
            restriction_id=restriction_id,
            location_file=location_file,
            created_by=user_id,
            last_modified_by=user_id,
        )
        db.add(new_page)
        db.flush()
        return new_page

    @staticmethod
    def update_page(
        db: Session,
        page: Page,
        user_id: str,
        name: str = None,
        description: str = None,
        page_text: str = None,
        comment: str = None,
        restriction_id: str = None,
    ) -> Page:
        """Update an existing page"""
        if name is not None:
            page.name = name
        if description is not None:
            page.description = description
        if page_text is not None:
            page.page = page_text
        if comment is not None:
            page.comment = comment
        if restriction_id is not None:
            page.restriction_id = restriction_id
        
        page.last_modified_by = user_id
        page.last_modified_on = datetime.now(timezone.utc)
        
        db.flush()
        return page

    @staticmethod
    def delete_page(db: Session, page: Page, user_id: str) -> bool:
        """
        Soft delete a page and delete associated file
        
        Args:
            db: Database session
            page: Page to delete
            user_id: User performing delete
            
        Returns:
            True if successful
        """
        try:
            # Delete associated file
            if page.location_file:
                PageService.delete_file(page.location_file)
            
            # Soft delete in database
            page.active = False
            page.last_modified_by = user_id
            page.last_modified_on = datetime.now(timezone.utc)
            
            db.flush()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete page: {str(e)}"
            )

    @staticmethod
    def hard_delete_orphaned_files(upload_dir: Path = None) -> int:
        """
        Delete files that no longer have corresponding database records
        
        Args:
            upload_dir: Upload directory to scan
            
        Returns:
            Number of files deleted
        """
        if upload_dir is None:
            upload_dir = PageService.get_upload_dir()
        
        deleted_count = 0
        
        if not upload_dir.exists():
            return deleted_count
        
        # This would need a database session
        # Typically run as a background task
        # For now, just return 0
        return deleted_count
