
"""
Records routes for CRUD operations
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from pypdf import PdfReader, PdfWriter

from app.database import get_db
from app.models import Record, Restriction, WorkStatus, KeywordName, KeywordLocation, Page, RecordAuthor, Author, AuthorType
from app.schemas import (
    RecordCreateRequest,
    RecordUpdateRequest,
    RecordResponse,
    RecordDetailResponse,
    RecordListResponse,
    RecordListItemResponse,
    RecordListDefaultResponse,
    RecordListDefaultItemResponse,
    RecordReducedResponse,
    RecordAuthorResponse,
    RecordConditionResponse,
    LoanTypeResponse,
    LetteringResponse,
    PublicationTypeResponse,
    PublisherResponse,
)
from app.utils.auth import get_current_user, optional_user
from app.utils.phonetics import generate_phonetic_codes
from config import config
from typing import Optional, List


def _get_combined_pdf_source(page: Page) -> Optional[str]:
    """Prefer restriction PDFs in gallery-style combined downloads when available."""
    return page.restriction_file or page.current_file or page.location_file

router = APIRouter(
    prefix="/records",
    tags=["records"],
)


# Public defaultlist endpoint for frontend/tests
@router.get("/defaultlist", response_model=RecordListDefaultResponse)
async def list_records_default(
    db: Session = Depends(get_db),
    title: Optional[str] = Query(None, description="Search by title"),
    signature: Optional[str] = Query(None, description="Search by signature"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    from sqlalchemy.orm import joinedload
    query = db.query(Record).filter(Record.active == True)
    query = query.options(
        joinedload(Record.keywords_names),
        joinedload(Record.keywords_locations),
        joinedload(Record.record_authors).joinedload(RecordAuthor.author),
        joinedload(Record.publisher),
    )
    if title:
        query = query.filter(Record.title.ilike(f"%{title}%"))
    if signature:
        query = query.filter(Record.signature.ilike(f"%{signature}%"))
    total = query.distinct().count()
    records = query.distinct().order_by(Record.signature.asc(), Record.title.asc()).offset(skip).limit(limit).all()
    return {
        "items": [
            RecordListDefaultItemResponse(
                id=record.id,
                title=record.title,
                description=record.description,
                signature=record.signature,
                comment=record.comment,
                loantype=record.loantype.loan if hasattr(record, "loantype") and record.loantype else None,
                keywords_names=", ".join(sorted([kw.name for kw in record.keywords_names])) if record.keywords_names else "",
                keywords_locations=", ".join(sorted([kw.name for kw in record.keywords_locations])) if record.keywords_locations else "",
                authors="; ".join([
                    f"{ra.author.last_name}{', ' + ra.author.first_name if ra.author.first_name else ''}"
                    for ra in sorted(record.record_authors, key=lambda x: x.order or 0)
                ]) if record.record_authors else "",
                publisher=f"{record.publisher.companyname}{' (' + record.publisher.town + ')' if record.publisher and record.publisher.town else ''}" if record.publisher else "",
                page_count=len(record.pages) if hasattr(record, "pages") else 0,
                nlf_fdb=record.nlf_fdb,
                pers_count=record.pers_count,
            )
            for record in records
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def ensure_record_write_permission(current_user):
    """Only admin and user_bibl may create/update/delete records."""
    if not (current_user.has_role("admin") or current_user.has_role("user_bibl")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only admin or user_bibl can modify records.",
        )


def parse_uuid_value(value, field_name: str) -> UUID:
    """Normalize UUID values from JSON payloads before SQLAlchemy uses them."""
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}",
        )


def process_keywords(db: Session, keywords_string: str, keyword_model):
    """
    Process comma-separated keywords string and return list of keyword objects.
    Creates new keywords if they don't exist.
    
    Args:
        db: Database session
        keywords_string: Comma-separated string of keywords
        keyword_model: Either KeywordName or KeywordLocation model class
        
    Returns:
        List of keyword model instances
    """
    if not keywords_string or not keywords_string.strip():
        return []
    
    keywords = []
    keyword_names = [kw.strip() for kw in keywords_string.split(",") if kw.strip()]
    
    for keyword_name in keyword_names:
        # Check if keyword already exists
        existing_keyword = db.query(keyword_model).filter(
            keyword_model.name == keyword_name
        ).first()
        
        if existing_keyword:
            keywords.append(existing_keyword)
        else:
            # Generate phonetic codes
            c_search, dblmeta_1, dblmeta_2 = generate_phonetic_codes(keyword_name)
            
            # Create new keyword
            new_keyword = keyword_model(
                name=keyword_name,
                c_search=c_search,
                dblmeta_1=dblmeta_1,
                dblmeta_2=dblmeta_2
            )
            db.add(new_keyword)
            db.flush()  # Flush to get the ID
            keywords.append(new_keyword)
    
    return keywords


def sync_record_authors(db: Session, record: Record, assignments, current_user_id):
    """Replace record-author relations with submitted assignments in stable order."""
    for existing in list(record.record_authors):
        db.delete(existing)
    db.flush()

    if not assignments:
        return

    for position, assignment in enumerate(assignments, start=1):
        author = db.query(Author).filter(Author.id == assignment.author_id, Author.active == True).first()
        if not author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Author not found: {assignment.author_id}",
            )

        authortype_id = assignment.authortype_id
        if authortype_id is not None:
            authortype = db.query(AuthorType).filter(AuthorType.id == authortype_id).first()
            if not authortype:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AuthorType not found: {authortype_id}",
                )

        relation = RecordAuthor(
            record_id=record.id,
            author_id=assignment.author_id,
            authortype_id=authortype_id,
            order=assignment.order if assignment.order is not None else position,
            created_by=current_user_id,
        )
        db.add(relation)


def parse_optional_date(value: Optional[str], field_name: str):
    """Parse optional ISO date string (YYYY-MM-DD) for date columns."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}. Expected YYYY-MM-DD",
        )


@router.get("", response_model=RecordListResponse)
async def list_records(
    db: Session = Depends(get_db),
    current_user = Depends(optional_user),
    title: Optional[str] = Query(None, description="Search by title"),
    signature: Optional[str] = Query(None, description="Search by signature"),
    keywords_names: Optional[str] = Query(None, description="Search by keywords names (comma-separated)"),
    keywords_locations: Optional[str] = Query(None, description="Search by keywords locations (comma-separated)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List all records with optional search filters
    Supports multiple keywords in names and locations (comma-separated)
    """
    from sqlalchemy.orm import joinedload
    
    # Base query with eager loading of relationships
    query = db.query(Record).filter(Record.active == True)
    
    # Eagerly load keywords relationships to avoid N+1 queries
    query = query.options(
        joinedload(Record.keywords_names),
        joinedload(Record.keywords_locations),
        joinedload(Record.record_authors).joinedload(RecordAuthor.author),
        joinedload(Record.publisher),
        joinedload(Record.restriction),
        joinedload(Record.workstatus)
    )

    if title:
        query = query.filter(Record.title.ilike(f"%{title}%"))

    if signature:
        query = query.filter(Record.signature.ilike(f"%{signature}%"))

    # Search by keywords_names - use subquery to avoid affecting main results
    if keywords_names:
        keyword_list = [kw.strip() for kw in keywords_names.split(",") if kw.strip()]
        if keyword_list:
            # Subquery to find record IDs that have matching keywords (case-insensitive, partial match)
            from sqlalchemy import or_
            keyword_conditions = [KeywordName.name.ilike(f"%{kw}%") for kw in keyword_list]
            subquery = db.query(Record.id).join(Record.keywords_names).filter(
                or_(*keyword_conditions)
            ).subquery()
            query = query.filter(Record.id.in_(subquery))

    # Search by keywords_locations - use subquery to avoid affecting main results
    if keywords_locations:
        keyword_list = [kw.strip() for kw in keywords_locations.split(",") if kw.strip()]
        if keyword_list:
            # Subquery to find record IDs that have matching keywords (case-insensitive, partial match)
            from sqlalchemy import or_
            keyword_conditions = [KeywordLocation.name.ilike(f"%{kw}%") for kw in keyword_list]
            subquery = db.query(Record.id).join(Record.keywords_locations).filter(
                or_(*keyword_conditions)
            ).subquery()
            query = query.filter(Record.id.in_(subquery))

    # Get total count
    total = query.distinct().count()

    # Get paginated results, sorted by signature ascending, then title
    records = query.distinct().order_by(Record.signature.asc(), Record.title.asc()).offset(skip).limit(limit).all()

    return {
        "items": [
            RecordListItemResponse(
                id=record.id,
                title=record.title,
                description=record.description,
                signature=record.signature,
                comment=record.comment,
                loantype=record.loantype.loan if record.loantype else None,
                loantype_subtype=(
                    record.loantype.subtype if record.loantype and record.loantype.subtype and (
                        current_user and (getattr(current_user, 'has_role', lambda r: False)("admin") or getattr(current_user, 'has_role', lambda r: False)("user_bibl"))
                    ) else None
                ),
                restriction_id=record.restriction_id,
                restriction=record.restriction.name if record.restriction else None,
                workstatus_id=record.workstatus_id,
                workstatus=record.workstatus.status if record.workstatus else None,
                keywords_names=", ".join(sorted([kw.name for kw in record.keywords_names])) if record.keywords_names else "",
                keywords_locations=", ".join(sorted([kw.name for kw in record.keywords_locations])) if record.keywords_locations else "",
                authors="; ".join([f"{ra.author.last_name}{', ' + ra.author.first_name if ra.author.first_name else ''}" for ra in sorted(record.record_authors, key=lambda x: x.order or 0)] if record.record_authors else []),
                publisher=f"{record.publisher.companyname}{' (' + record.publisher.town + ')' if record.publisher and record.publisher.town else ''}" if record.publisher else "",
                created_on=record.created_on,
                created_by=record.created_by,
                entered_on=record.enter_date,
                page_count=db.query(func.count(Page.id)).filter(
                    Page.record_id == record.id,
                    Page.active == True
                ).scalar() or 0,
                nlf_fdb=record.nlf_fdb,
                pers_count=record.pers_count,
            )
            for record in records
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }

    if signature:
        query = query.filter(Record.signature.ilike(f"%{signature}%"))

    # Search by keywords_names - use subquery to avoid affecting main results
    if keywords_names:
        keyword_list = [kw.strip() for kw in keywords_names.split(",") if kw.strip()]
        if keyword_list:
            # Subquery to find record IDs that have matching keywords (case-insensitive, partial match)
            from sqlalchemy import or_
            keyword_conditions = [KeywordName.name.ilike(f"%{kw}%") for kw in keyword_list]
            subquery = db.query(Record.id).join(Record.keywords_names).filter(
                or_(*keyword_conditions)
            ).subquery()
            query = query.filter(Record.id.in_(subquery))

    # Search by keywords_locations - use subquery to avoid affecting main results
    if keywords_locations:
        keyword_list = [kw.strip() for kw in keywords_locations.split(",") if kw.strip()]
        if keyword_list:
            # Subquery to find record IDs that have matching keywords (case-insensitive, partial match)
            from sqlalchemy import or_
            keyword_conditions = [KeywordLocation.name.ilike(f"%{kw}%") for kw in keyword_list]
            subquery = db.query(Record.id).join(Record.keywords_locations).filter(
                or_(*keyword_conditions)
            ).subquery()
            query = query.filter(Record.id.in_(subquery))

    # Get total count
    total = query.distinct().count()

    # Get paginated results, sorted by signature ascending, then title
    records = query.distinct().order_by(Record.signature.asc(), Record.title.asc()).offset(skip).limit(limit).all()

    return {
        "items": [
            RecordListDefaultItemResponse(
                id=record.id,
                title=record.title,
                description=record.description,
                signature=record.signature,
                comment=record.comment,
                loantype=record.loantype.loan if record.loantype else None,
                keywords_names=", ".join(sorted([kw.name for kw in record.keywords_names])) if record.keywords_names else "",
                keywords_locations=", ".join(sorted([kw.name for kw in record.keywords_locations])) if record.keywords_locations else "",
                authors="; ".join([f"{ra.author.last_name}{', ' + ra.author.first_name if ra.author.first_name else ''}" for ra in sorted(record.record_authors, key=lambda x: x.order or 0)] if record.record_authors else []),
                publisher=f"{record.publisher.companyname}{' (' + record.publisher.town + ')' if record.publisher.town else ''}" if record.publisher else "",
                page_count=db.query(func.count(Page.id)).filter(
                    Page.record_id == record.id,
                    Page.active == True
                ).scalar() or 0,
                nlf_fdb=record.nlf_fdb,
                pers_count=record.pers_count,
            )
            for record in records
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }



@router.get("/reduced", response_model=List[RecordReducedResponse])
async def list_reduced_records(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    signature: Optional[str] = Query(None, description="Filter by signature (partial match)"),
):
    """
    List reduced records with only id, name and signature.
    Sorted ascending by signature.
    """
    query = db.query(Record).filter(Record.active == True)

    if signature:
        query = query.filter(Record.signature.ilike(f"%{signature}%"))

    records = query.order_by(Record.signature.asc(), Record.title.asc()).all()

    return [RecordReducedResponse(id=record.id, name=record.title, signature=record.signature) for record in records]


@router.get("/{record_id}", response_model=RecordDetailResponse)
async def get_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get a specific record by ID with all relationships (keywords, authors, publisher, etc.)
    """
    parsed_record_id = parse_uuid_value(record_id, "record_id")
    record = (
        db.query(Record)
        .options(
            joinedload(Record.keywords_names),
            joinedload(Record.keywords_locations),
            joinedload(Record.record_authors).joinedload(RecordAuthor.author),
            joinedload(Record.record_authors).joinedload(RecordAuthor.authortype),
            joinedload(Record.record_condition),
            joinedload(Record.loantype),
            joinedload(Record.lettering),
            joinedload(Record.publicationtype),
            joinedload(Record.publisher),
        )
        .filter(Record.id == parsed_record_id, Record.active == True)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    base = RecordResponse.model_validate(record, from_attributes=True)
    return RecordDetailResponse(
        **base.model_dump(),
        keywords_names=", ".join(sorted([kw.name for kw in record.keywords_names])) if record.keywords_names else "",
        keywords_locations=", ".join(sorted([kw.name for kw in record.keywords_locations])) if record.keywords_locations else "",
        record_condition=RecordConditionResponse.model_validate(record.record_condition, from_attributes=True) if record.record_condition else None,
        loantype=LoanTypeResponse.model_validate(record.loantype, from_attributes=True) if record.loantype else None,
        lettering=LetteringResponse.model_validate(record.lettering, from_attributes=True) if record.lettering else None,
        publicationtype=PublicationTypeResponse.model_validate(record.publicationtype, from_attributes=True) if record.publicationtype else None,
        publisher=PublisherResponse.model_validate(record.publisher, from_attributes=True) if record.publisher else None,
        record_authors=[RecordAuthorResponse.model_validate(ra, from_attributes=True) for ra in record.record_authors],
    )


@router.get("/{record_id}/download-combined-pdf")
async def download_combined_pdf(
    record_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Generate and download a combined PDF with all pages of a record.
    Each page's PDF is watermarked with user information before combining.
    """
    # Get the record
    parsed_record_id = parse_uuid_value(record_id, "record_id")
    record = db.query(Record).filter(Record.id == parsed_record_id, Record.active == True).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    

    restriction_message = ""
    if record.restriction_id and record.restriction_id != UUID("00000000-0000-0000-0000-000000000001"):
        restriction_message = "Restricted"

    # Get all pages for this record that have PDF files, ordered by name
    pages = (
        db.query(Page)
        .options(joinedload(Page.record))
        .filter(
            Page.record_id == parsed_record_id,
            Page.active == True,
            or_(
                Page.restriction_file.isnot(None),
                Page.current_file.isnot(None),
                Page.location_file.isnot(None),
            )
        )
        .order_by(Page.order_by.asc().nulls_last(), Page.name.asc())
        .all()
    )
    
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF pages found for this record"
        )

    try:
        from app.services.pdf_watermark_service import create_watermarked_pdf
        from app.utils.public_links import build_record_public_url_pdf

        # Create a PDF writer to combine all pages
        combined_writer = PdfWriter()
        downloaded_at = datetime.now()
        
        # Process each page
        for page in pages:
            source_pdf = _get_combined_pdf_source(page)
            if not source_pdf:
                continue

            source_pdf_path = (config.UPLOAD_DIRECTORY / source_pdf).resolve()
            
            if not source_pdf_path.exists() or not source_pdf_path.is_file():
                # Skip pages where PDF file is missing
                continue
            
            # Generate watermarked PDF for this page
            watermarked_bytes = create_watermarked_pdf(
                source_pdf=source_pdf_path,
                username=current_user.username,
                downloaded_at=downloaded_at,
                record_name=record.title,
                record_signature=record.signature,
                record_pdf_url=build_record_public_url_pdf(page.record.id) if page.record else None,
                page_text=page.name,
                watermark_image_path=config.get_watermark_image_path(),
                watermark_copyright=config.WATERMARK_COPYRIGHT,
                restriction_message=restriction_message,
            )
            
            # Read the watermarked PDF and append all its pages to the combined PDF
            watermarked_reader = PdfReader(BytesIO(watermarked_bytes))
            for pdf_page in watermarked_reader.pages:
                combined_writer.add_page(pdf_page)
        
        # Check if we have any pages to output
        if len(combined_writer.pages) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid PDF pages could be processed"
            )
        
        # Write combined PDF to bytes
        output = BytesIO()
        combined_writer.write(output)
        output.seek(0)
        combined_bytes = output.read()
        
        # Create safe filename from record title or signature
        safe_filename = record.title or record.signature or record_id
        # Remove or replace characters that are problematic in filenames
        safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in safe_filename)
        safe_filename = safe_filename[:100]  # Limit length
        download_name = f"{safe_filename}.pdf"
        
        return Response(
            content=combined_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_name}"',
                "Cache-Control": "no-store",
            },
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate combined PDF: {str(exc)}",
        )


@router.post("", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    data: RecordCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Create a new record
    Only users with 'admin' or 'user_bibl' role can create records
        # Check user permissions
        if not (current_user.has_role("admin") or current_user.has_role("user_bibl")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Only admin or user_bibl can create records."
            )
    
    """
    ensure_record_write_permission(current_user)

    restriction_id = data.restriction_id
    workstatus_id = data.workstatus_id

    # Validate that restriction exists
    restriction = db.query(Restriction).filter(Restriction.id == restriction_id).first()
    if not restriction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restriction not found"
        )

    # Validate that workstatus exists
    workstatus = db.query(WorkStatus).filter(WorkStatus.id == workstatus_id).first()
    if not workstatus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WorkStatus not found"
        )

    try:
        record = Record(
            title=data.title,
            description=data.description,
            signature=data.signature,
            signature2=data.signature2,
            subtitle=data.subtitle,
            comment=data.comment,
            year=data.year,
            isbn=data.isbn,
            number_pages=data.number_pages,
            edition=data.edition,
            reihe=data.reihe,
            volume=data.volume,
            jahrgang=data.jahrgang,
            enter_information=data.enter_information,
            indecies=data.indecies,
            enter_date=parse_optional_date(data.enter_date, "enter_date"),
            sort_out_date=parse_optional_date(data.sort_out_date, "sort_out_date"),
            bibl_nr=data.bibl_nr,
            restriction_id=restriction_id,
            workstatus_id=workstatus_id,
            record_condition_id=data.record_condition_id,
            loantype_id=data.loantype_id,
            lettering_id=data.lettering_id,
            publicationtype_id=data.publicationtype_id,
            publisher_id=data.publisher_id,
            nlf_fdb=data.nlf_fdb,
            pers_count=data.pers_count,
            created_by=current_user.id,
        )

        db.add(record)
        db.flush()  # Flush to get the record ID

        # Process keywords_names
        if data.keywords_names:
            keywords_names = process_keywords(db, data.keywords_names, KeywordName)
            record.keywords_names = keywords_names

        # Process keywords_locations
        if data.keywords_locations:
            keywords_locations = process_keywords(db, data.keywords_locations, KeywordLocation)
            record.keywords_locations = keywords_locations

        if data.record_authors is not None:
            sync_record_authors(db, record, data.record_authors, current_user.id)

        db.commit()
        db.refresh(record)

        return RecordResponse.model_validate(record, from_attributes=True)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create record: {str(e)}"
        )


@router.put("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: str,
    data: RecordUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update a record
    Only users with 'admin' or 'user_bibl' role can update records
        # Check user permissions
        if not (current_user.has_role("admin") or current_user.has_role("user_bibl")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Only admin or user_bibl can update records."
            )
    
    """
    ensure_record_write_permission(current_user)
    data_dict = data.model_dump(exclude_unset=True)

    parsed_record_id = parse_uuid_value(record_id, "record_id")
    record = db.query(Record).filter(Record.id == parsed_record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    restriction_id = record.restriction_id
    if "restriction_id" in data_dict and data_dict.get("restriction_id") is not None:
        restriction_id = data_dict.get("restriction_id")

    # Validate restriction if changed
    if "restriction_id" in data_dict:
        restriction = db.query(Restriction).filter(Restriction.id == restriction_id).first()
        if not restriction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Restriction not found"
            )

    workstatus_id = record.workstatus_id
    if "workstatus_id" in data_dict and data_dict.get("workstatus_id") is not None:
        workstatus_id = data_dict.get("workstatus_id")

    # Validate workstatus if changed
    if "workstatus_id" in data_dict:
        workstatus = db.query(WorkStatus).filter(WorkStatus.id == workstatus_id).first()
        if not workstatus:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WorkStatus not found"
            )

    try:
        # Update basic fields
        for field in (
            "title", "description", "signature", "signature2", "subtitle", "comment",
            "year", "isbn", "number_pages", "edition", "reihe", "volume", "jahrgang",
            "enter_information", "indecies", "bibl_nr", "record_condition_id", "loantype_id",
            "lettering_id", "publicationtype_id", "publisher_id", "nlf_fdb", "pers_count"
        ):
            if field in data_dict:
                setattr(record, field, data_dict[field])

        if "enter_date" in data_dict:
            record.enter_date = parse_optional_date(data_dict.get("enter_date"), "enter_date")
        if "sort_out_date" in data_dict:
            record.sort_out_date = parse_optional_date(data_dict.get("sort_out_date"), "sort_out_date")

        record.restriction_id = restriction_id
        record.workstatus_id = workstatus_id
        record.last_modified_by = current_user.id

        # Update keywords_names
        if "keywords_names" in data_dict:
            keywords_names = process_keywords(db, data_dict.get("keywords_names"), KeywordName)
            record.keywords_names = keywords_names

        # Update keywords_locations
        if "keywords_locations" in data_dict:
            keywords_locations = process_keywords(db, data_dict.get("keywords_locations"), KeywordLocation)
            record.keywords_locations = keywords_locations

        if "record_authors" in data_dict:
            sync_record_authors(db, record, data.record_authors, current_user.id)

        db.commit()
        db.refresh(record)

        return RecordResponse.model_validate(record, from_attributes=True)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update record: {str(e)}"
        )


@router.delete("/{record_id}")
async def delete_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Delete a record (soft delete)
    """
    ensure_record_write_permission(current_user)

    parsed_record_id = parse_uuid_value(record_id, "record_id")
    record = db.query(Record).filter(Record.id == parsed_record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    try:
        record.active = False
        record.last_modified_by = current_user.id

        db.commit()

        return {"message": "Record deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete record: {str(e)}"
        )


@router.get("/metadata/restrictions")
async def get_restrictions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get all restrictions for dropdown selection
    """
    restrictions = db.query(Restriction).all()

    return {
        "items": [
            {
                "id": str(restriction.id),
                "name": restriction.name,
            }
            for restriction in restrictions
        ]
    }


@router.get("/metadata/restrictions/by-name")
async def get_restriction_id_by_name(
    name: str = Query(..., min_length=1, description="Restriction name (exact match, case-insensitive)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get restriction ID by restriction name.
    """
    normalized_name = name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restriction name must not be empty"
        )

    restriction = db.query(Restriction).filter(Restriction.name.ilike(normalized_name)).first()

    if not restriction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restriction not found"
        )

    return {
        "id": str(restriction.id),
        "name": restriction.name,
    }


@router.get("/metadata/workstatus")
async def get_workstatus(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get all workstatus for dropdown selection
    """
    from app.models import WorkStatusArea
    
    workstatus_list = db.query(WorkStatus).all()

    return {
        "items": [
            {
                "id": str(ws.id),
                "status": ws.status,
                "area": ws.area.area if ws.area else None,
            }
            for ws in workstatus_list
        ]
    }


@router.get("/metadata/workstatus/by-name")
async def get_workstatus_id_by_name(
    name: str = Query(..., min_length=1, description="Workstatus name (exact match, case-insensitive)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get workstatus ID by status name.
    """
    normalized_name = name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workstatus name must not be empty"
        )

    workstatus = db.query(WorkStatus).filter(WorkStatus.status.ilike(normalized_name)).first()

    if not workstatus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workstatus not found"
        )

    return {
        "id": str(workstatus.id),
        "status": workstatus.status,
        "area": workstatus.area.area if workstatus.area else None,
    }
