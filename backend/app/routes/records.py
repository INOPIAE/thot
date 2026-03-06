"""
Records routes for CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import Record, Restriction, WorkStatus, KeywordName, KeywordLocation
from app.utils.auth import get_current_user
from app.utils.phonetics import generate_phonetic_codes
from typing import Optional, List

router = APIRouter(
    prefix="/records",
    tags=["records"],
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


@router.get("")
async def list_records(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
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

    # Get paginated results
    records = query.distinct().offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": str(record.id),
                "title": record.title,
                "description": record.description,
                "signature": record.signature,
                "comment": record.comment,
                "restriction_id": str(record.restriction_id),
                "restriction": record.restriction.name if record.restriction else None,
                "workstatus_id": str(record.workstatus_id),
                "workstatus": record.workstatus.status if record.workstatus else None,
                "keywords_names": ", ".join(sorted([kw.name for kw in record.keywords_names])) if record.keywords_names else "",
                "keywords_locations": ", ".join(sorted([kw.name for kw in record.keywords_locations])) if record.keywords_locations else "",
                "created_on": record.created_on.isoformat() if record.created_on else None,
                "created_by": str(record.created_by) if record.created_by else None,
            }
            for record in records
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{record_id}")
async def get_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get a specific record by ID
    """
    record = db.query(Record).filter(Record.id == record_id, Record.active == True).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    return {
        "id": str(record.id),
        "title": record.title,
        "description": record.description,
        "signature": record.signature,
        "comment": record.comment,
        "restriction_id": str(record.restriction_id),
        "restriction": record.restriction.name if record.restriction else None,
        "workstatus_id": str(record.workstatus_id),
        "workstatus": record.workstatus.status if record.workstatus else None,
        "keywords_names": ", ".join(sorted([kw.name for kw in record.keywords_names])) if record.keywords_names else "",
        "keywords_locations": ", ".join(sorted([kw.name for kw in record.keywords_locations])) if record.keywords_locations else "",
        "created_on": record.created_on.isoformat() if record.created_on else None,
        "created_by": str(record.created_by) if record.created_by else None,
        "last_modified_on": record.last_modified_on.isoformat() if record.last_modified_on else None,
        "last_modified_by": str(record.last_modified_by) if record.last_modified_by else None,
    }


@router.post("")
async def create_record(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Create a new record
    """
    # Validate that restriction exists
    restriction = db.query(Restriction).filter(Restriction.id == data.get("restriction_id")).first()
    if not restriction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restriction not found"
        )

    # Validate that workstatus exists
    workstatus = db.query(WorkStatus).filter(WorkStatus.id == data.get("workstatus_id")).first()
    if not workstatus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WorkStatus not found"
        )

    try:
        record = Record(
            title=data.get("title"),
            description=data.get("description"),
            signature=data.get("signature"),
            comment=data.get("comment"),
            restriction_id=data.get("restriction_id"),
            workstatus_id=data.get("workstatus_id"),
            created_by=current_user.id,
        )

        db.add(record)
        db.flush()  # Flush to get the record ID

        # Process keywords_names
        if data.get("keywords_names"):
            keywords_names = process_keywords(db, data.get("keywords_names"), KeywordName)
            record.keywords_names = keywords_names

        # Process keywords_locations
        if data.get("keywords_locations"):
            keywords_locations = process_keywords(db, data.get("keywords_locations"), KeywordLocation)
            record.keywords_locations = keywords_locations

        db.commit()
        db.refresh(record)

        return {
            "id": str(record.id),
            "title": record.title,
            "description": record.description,
            "signature": record.signature,
            "comment": record.comment,
            "restriction_id": str(record.restriction_id),
            "workstatus_id": str(record.workstatus_id),
            "keywords_names": ", ".join([kw.name for kw in record.keywords_names]) if record.keywords_names else "",
            "keywords_locations": ", ".join([kw.name for kw in record.keywords_locations]) if record.keywords_locations else "",
            "message": "Record created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create record: {str(e)}"
        )


@router.put("/{record_id}")
async def update_record(
    record_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update a record
    """
    record = db.query(Record).filter(Record.id == record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    # Validate restriction if changed
    if "restriction_id" in data:
        restriction = db.query(Restriction).filter(Restriction.id == data.get("restriction_id")).first()
        if not restriction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Restriction not found"
            )

    # Validate workstatus if changed
    if "workstatus_id" in data:
        workstatus = db.query(WorkStatus).filter(WorkStatus.id == data.get("workstatus_id")).first()
        if not workstatus:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WorkStatus not found"
            )

    try:
        # Update basic fields
        record.title = data.get("title", record.title)
        record.description = data.get("description", record.description)
        record.signature = data.get("signature", record.signature)
        record.comment = data.get("comment", record.comment)
        record.restriction_id = data.get("restriction_id", record.restriction_id)
        record.workstatus_id = data.get("workstatus_id", record.workstatus_id)
        record.last_modified_by = current_user.id

        # Update keywords_names
        if "keywords_names" in data:
            keywords_names = process_keywords(db, data.get("keywords_names"), KeywordName)
            record.keywords_names = keywords_names

        # Update keywords_locations
        if "keywords_locations" in data:
            keywords_locations = process_keywords(db, data.get("keywords_locations"), KeywordLocation)
            record.keywords_locations = keywords_locations

        db.commit()
        db.refresh(record)

        return {
            "id": str(record.id),
            "title": record.title,
            "description": record.description,
            "signature": record.signature,
            "comment": record.comment,
            "restriction_id": str(record.restriction_id),
            "workstatus_id": str(record.workstatus_id),
            "keywords_names": ", ".join([kw.name for kw in record.keywords_names]) if record.keywords_names else "",
            "keywords_locations": ", ".join([kw.name for kw in record.keywords_locations]) if record.keywords_locations else "",
            "message": "Record updated successfully"
        }
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
    record = db.query(Record).filter(Record.id == record_id).first()

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
