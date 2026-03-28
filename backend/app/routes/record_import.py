"""Admin-only record import routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.record_import_service import import_records_from_xlsx
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/admin/records-import",
    tags=["admin-record-import"],
)


def _require_admin(current_user):
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )


@router.post("/xlsx")
async def import_records_xlsx(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_admin(current_user)

    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = import_records_from_xlsx(file_bytes, db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")

    return {
        "imported": result.imported,
        "skipped": result.skipped,
        "errors": result.errors,
    }
