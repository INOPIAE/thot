"""
Records routes for CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import Record, Restriction, WorkStatus
from app.utils import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

router = APIRouter(
    prefix="/records",
    tags=["records"],
)

security = HTTPBearer()


async def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user from JWT token
    """
    token = credentials.credentials
    user_id = decode_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    from app.services import UserService
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


@router.get("")
async def list_records(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    title: Optional[str] = Query(None, description="Search by title"),
    signature: Optional[str] = Query(None, description="Search by signature"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List all records with optional search filters
    """
    query = db.query(Record).filter(Record.active == True)

    if title:
        query = query.filter(Record.title.ilike(f"%{title}%"))

    if signature:
        query = query.filter(Record.signature.ilike(f"%{signature}%"))

    # Get total count
    total = query.count()

    # Get paginated results
    records = query.offset(skip).limit(limit).all()

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
        record.title = data.get("title", record.title)
        record.description = data.get("description", record.description)
        record.signature = data.get("signature", record.signature)
        record.comment = data.get("comment", record.comment)
        record.restriction_id = data.get("restriction_id", record.restriction_id)
        record.workstatus_id = data.get("workstatus_id", record.workstatus_id)
        record.last_modified_by = current_user.id

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
