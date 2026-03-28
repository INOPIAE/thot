"""
Library metadata routes – CRUD for bibliographic lookup tables:
  - LoanType
  - Language
  - Author / AuthorType / RecordAuthor
  - Publisher
  - PublicationType
  - RecordCondition
  - Lettering
  - KeywordRecord (bibliographic Schlagwörter)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import (
    LoanType, Language, RecordsLanguage,
    Author, AuthorType, RecordAuthor,
    Publisher, PublicationType,
    RecordCondition, Lettering,
    KeywordRecord, RecordsKeywordsRecord,
)
from app.utils.auth import get_current_user
from app.utils.phonetics import generate_phonetic_codes

router = APIRouter(
    prefix="/library-metadata",
    tags=["library-metadata"],
)


def _require_admin_or_record(current_user):
    if not (current_user.has_role("admin") or current_user.has_role("user_record")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def _parse_uuid(value, field: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")


# ------------------------------------------------------------------ #
# LoanType                                                             #
# ------------------------------------------------------------------ #

@router.get("/loantypes")
async def list_loantypes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(LoanType).all()
    return {"items": [{"id": str(i.id), "loan": i.loan, "subtype": i.subtype, "comment": i.comment} for i in items]}


@router.post("/loantypes")
async def create_loantype(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = LoanType(loan=data.get("loan"), subtype=data.get("subtype"), comment=data.get("comment"))
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "loan": item.loan, "subtype": item.subtype, "comment": item.comment}


@router.put("/loantypes/{item_id}")
async def update_loantype(item_id: str, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(LoanType).filter(LoanType.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="LoanType not found")
    if "loan" in data:
        item.loan = data["loan"]
    if "subtype" in data:
        item.subtype = data["subtype"]
    if "comment" in data:
        item.comment = data["comment"]
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "loan": item.loan, "subtype": item.subtype, "comment": item.comment}


@router.delete("/loantypes/{item_id}")
async def delete_loantype(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(LoanType).filter(LoanType.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="LoanType not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# Language                                                             #
# ------------------------------------------------------------------ #

@router.get("/languages")
async def list_languages(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(Language).order_by(Language.language).all()
    return {"items": [{"id": str(i.id), "language": i.language} for i in items]}


@router.post("/languages")
async def create_language(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    lang = data.get("language", "").strip()
    if not lang:
        raise HTTPException(status_code=400, detail="language is required")
    existing = db.query(Language).filter(Language.language == lang).first()
    if existing:
        return {"id": str(existing.id), "language": existing.language}
    item = Language(language=lang)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "language": item.language}


@router.delete("/languages/{item_id}")
async def delete_language(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(Language).filter(Language.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="Language not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# AuthorType                                                           #
# ------------------------------------------------------------------ #

@router.get("/authortypes")
async def list_authortypes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(AuthorType).order_by(AuthorType.authortype).all()
    return {"items": [{"id": str(i.id), "authortype": i.authortype} for i in items]}


@router.post("/authortypes")
async def create_authortype(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    val = data.get("authortype", "").strip()
    if not val:
        raise HTTPException(status_code=400, detail="authortype is required")
    existing = db.query(AuthorType).filter(AuthorType.authortype == val).first()
    if existing:
        return {"id": str(existing.id), "authortype": existing.authortype}
    item = AuthorType(authortype=val)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "authortype": item.authortype}


@router.delete("/authortypes/{item_id}")
async def delete_authortype(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(AuthorType).filter(AuthorType.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="AuthorType not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# Author                                                               #
# ------------------------------------------------------------------ #

@router.get("/authors")
async def list_authors(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = db.query(Author).filter(Author.active == True)
    if search:
        query = query.filter(Author.last_name.ilike(f"%{search}%"))
    total = query.count()
    items = query.order_by(Author.last_name, Author.first_name).offset(skip).limit(limit).all()
    return {
        "items": [
            {"id": str(i.id), "first_name": i.first_name, "last_name": i.last_name, "title": i.title}
            for i in items
        ],
        "total": total,
    }


@router.post("/authors")
async def create_author(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    last_name = data.get("last_name", "").strip()
    if not last_name:
        raise HTTPException(status_code=400, detail="last_name is required")
    item = Author(
        first_name=data.get("first_name"),
        last_name=last_name,
        title=data.get("title"),
        created_by=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "first_name": item.first_name, "last_name": item.last_name, "title": item.title}


@router.put("/authors/{item_id}")
async def update_author(item_id: str, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(Author).filter(Author.id == _parse_uuid(item_id, "item_id"), Author.active == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Author not found")
    if "first_name" in data:
        item.first_name = data["first_name"]
    if "last_name" in data:
        item.last_name = data["last_name"]
    if "title" in data:
        item.title = data["title"]
    item.last_modified_by = current_user.id
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "first_name": item.first_name, "last_name": item.last_name, "title": item.title}


@router.delete("/authors/{item_id}")
async def delete_author(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(Author).filter(Author.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="Author not found")
    item.active = False
    item.last_modified_by = current_user.id
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# Publisher                                                            #
# ------------------------------------------------------------------ #

@router.get("/publishers")
async def list_publishers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    query = db.query(Publisher).filter(Publisher.active == True)
    if search:
        query = query.filter(Publisher.companyname.ilike(f"%{search}%"))
    total = query.count()
    items = query.order_by(Publisher.companyname).offset(skip).limit(limit).all()
    return {
        "items": [
            {"id": str(i.id), "companyname": i.companyname, "town": i.town}
            for i in items
        ],
        "total": total,
    }


@router.post("/publishers")
async def create_publisher(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    name = data.get("companyname", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="companyname is required")
    item = Publisher(companyname=name, town=data.get("town"), created_by=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "companyname": item.companyname, "town": item.town}


@router.put("/publishers/{item_id}")
async def update_publisher(item_id: str, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(Publisher).filter(Publisher.id == _parse_uuid(item_id, "item_id"), Publisher.active == True).first()
    if not item:
        raise HTTPException(status_code=404, detail="Publisher not found")
    if "companyname" in data:
        item.companyname = data["companyname"]
    if "town" in data:
        item.town = data["town"]
    item.last_modified_by = current_user.id
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "companyname": item.companyname, "town": item.town}


@router.delete("/publishers/{item_id}")
async def delete_publisher(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(Publisher).filter(Publisher.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="Publisher not found")
    item.active = False
    item.last_modified_by = current_user.id
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# PublicationType                                                      #
# ------------------------------------------------------------------ #

@router.get("/publicationtypes")
async def list_publicationtypes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(PublicationType).order_by(PublicationType.publicationtype).all()
    return {"items": [{"id": str(i.id), "publicationtype": i.publicationtype} for i in items]}


@router.post("/publicationtypes")
async def create_publicationtype(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    val = data.get("publicationtype", "").strip()
    if not val:
        raise HTTPException(status_code=400, detail="publicationtype is required")
    existing = db.query(PublicationType).filter(PublicationType.publicationtype == val).first()
    if existing:
        return {"id": str(existing.id), "publicationtype": existing.publicationtype}
    item = PublicationType(publicationtype=val)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "publicationtype": item.publicationtype}


@router.delete("/publicationtypes/{item_id}")
async def delete_publicationtype(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(PublicationType).filter(PublicationType.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="PublicationType not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# RecordCondition                                                      #
# ------------------------------------------------------------------ #

@router.get("/record-conditions")
async def list_record_conditions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(RecordCondition).order_by(RecordCondition.condition).all()
    return {"items": [{"id": str(i.id), "condition": i.condition} for i in items]}


@router.post("/record-conditions")
async def create_record_condition(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    val = data.get("condition", "").strip()
    if not val:
        raise HTTPException(status_code=400, detail="condition is required")
    existing = db.query(RecordCondition).filter(RecordCondition.condition == val).first()
    if existing:
        return {"id": str(existing.id), "condition": existing.condition}
    item = RecordCondition(condition=val)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "condition": item.condition}


@router.delete("/record-conditions/{item_id}")
async def delete_record_condition(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(RecordCondition).filter(RecordCondition.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="RecordCondition not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# Lettering                                                            #
# ------------------------------------------------------------------ #

@router.get("/letterings")
async def list_letterings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items = db.query(Lettering).order_by(Lettering.lettering).all()
    return {"items": [{"id": str(i.id), "lettering": i.lettering} for i in items]}


@router.post("/letterings")
async def create_lettering(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    val = data.get("lettering", "").strip()
    if not val:
        raise HTTPException(status_code=400, detail="lettering is required")
    existing = db.query(Lettering).filter(Lettering.lettering == val).first()
    if existing:
        return {"id": str(existing.id), "lettering": existing.lettering}
    item = Lettering(lettering=val)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "lettering": item.lettering}


@router.delete("/letterings/{item_id}")
async def delete_lettering(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(Lettering).filter(Lettering.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="Lettering not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}


# ------------------------------------------------------------------ #
# KeywordRecord (bibliographic Schlagwörter)                           #
# ------------------------------------------------------------------ #

@router.get("/keyword-records")
async def list_keyword_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = db.query(KeywordRecord)
    if search:
        query = query.filter(KeywordRecord.name.ilike(f"%{search}%"))
    total = query.count()
    items = query.order_by(KeywordRecord.name).offset(skip).limit(limit).all()
    return {
        "items": [{"id": str(i.id), "name": i.name} for i in items],
        "total": total,
    }


@router.post("/keyword-records")
async def create_keyword_record(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    existing = db.query(KeywordRecord).filter(KeywordRecord.name == name).first()
    if existing:
        return {"id": str(existing.id), "name": existing.name}
    c_search, dblmeta_1, dblmeta_2 = generate_phonetic_codes(name)
    item = KeywordRecord(name=name, c_search=c_search, dblmeta_1=dblmeta_1, dblmeta_2=dblmeta_2)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": str(item.id), "name": item.name}


@router.delete("/keyword-records/{item_id}")
async def delete_keyword_record(item_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _require_admin_or_record(current_user)
    item = db.query(KeywordRecord).filter(KeywordRecord.id == _parse_uuid(item_id, "item_id")).first()
    if not item:
        raise HTTPException(status_code=404, detail="KeywordRecord not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
