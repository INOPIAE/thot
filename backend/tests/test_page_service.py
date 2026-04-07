import io
import os
import tempfile
import uuid
import pytest
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.services.page_service import PageService
from app.models import Page

class DummyFile:
    def __init__(self, filename, content):
        self.filename = filename
        self._content = content
    async def read(self):
        return self._content

class DummyConfig:
    UPLOAD_DIRECTORY = Path(tempfile.gettempdir()) / "nlf_test_uploads"
    ALLOWED_FILE_EXTENSIONS = [".pdf", ".txt"]
    MAX_UPLOAD_SIZE = 1024 * 1024  # 1 MB

@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    monkeypatch.setattr("app.services.page_service.config", DummyConfig)
    yield
    # Cleanup test upload dir
    upload_dir = DummyConfig.UPLOAD_DIRECTORY
    if upload_dir.exists():
        for f in upload_dir.rglob("*"):
            if f.is_file():
                f.unlink()
        for d in reversed(list(upload_dir.rglob("*"))):
            if d.is_dir():
                d.rmdir()
        if upload_dir.exists():
            upload_dir.rmdir()

def test_get_upload_dir_creates_dir():
    dir_path = PageService.get_upload_dir()
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_get_record_upload_dir_creates_dir():
    record_id = str(uuid.uuid4())
    dir_path = PageService.get_record_upload_dir(record_id)
    assert dir_path.exists()
    assert dir_path.is_dir()
    assert record_id in str(dir_path)

def test_validate_file_accepts_allowed():
    file = DummyFile("test.pdf", b"abc")
    assert PageService.validate_file(file)

def test_validate_file_rejects_extension():
    file = DummyFile("test.exe", b"abc")
    with pytest.raises(HTTPException) as exc:
        PageService.validate_file(file)
    assert exc.value.status_code == 400
    assert "not allowed" in exc.value.detail

def test_validate_file_rejects_none():
    with pytest.raises(HTTPException) as exc:
        PageService.validate_file(None)
    assert exc.value.status_code == 400
    assert "No file provided" in exc.value.detail

@pytest.mark.asyncio
async def test_save_file_and_delete_file():
    record_id = str(uuid.uuid4())
    content = b"testdata"
    file = DummyFile("test.pdf", content)
    rel_path = None
    # Save file
    rel_path = await PageService.save_file(file, record_id)
    assert rel_path.endswith(".pdf")
    # File exists
    abs_path = DummyConfig.UPLOAD_DIRECTORY / rel_path
    assert abs_path.exists()
    # Delete file
    assert PageService.delete_file(rel_path)
    assert not abs_path.exists()

@pytest.mark.asyncio
async def test_save_file_too_large():
    record_id = str(uuid.uuid4())
    content = b"a" * (DummyConfig.MAX_UPLOAD_SIZE + 1)
    file = DummyFile("test.pdf", content)
    with pytest.raises(HTTPException) as exc:
        await PageService.save_file(file, record_id)
    assert exc.value.status_code == 413

# Database-dependent tests (mocked)
def test_get_page_and_get_pages_for_record(monkeypatch):
    class DummyDB:
        def query(self, model):
            class Q:
                def filter(self, *a, **kw):
                    class F:
                        def first(self): return "page"
                        def all(self): return ["page1", "page2"]
                    return F()
            return Q()
    db = DummyDB()
    assert PageService.get_page(db, "pid") == "page"
    assert PageService.get_pages_for_record(db, "rid") == ["page1", "page2"]

def test_create_update_delete_page(monkeypatch):
    class DummyPage:
        def __init__(self):
            self.name = None
            self.description = None
            self.page = None
            self.comment = None
            self.restriction_id = None
            self.last_modified_by = None
            self.last_modified_on = None
            self.active = True
            self.location_file = None
    class DummyDB:
        def add(self, obj): self.obj = obj
        def flush(self): pass
        def rollback(self): self.rolled_back = True
    db = DummyDB()
    # create_page
    page = PageService.create_page(db, "n", "rid", "resid", "uid", "desc", "pagetxt", "comment", "loc.pdf")
    assert page.name == "n"
    # update_page
    updated = PageService.update_page(db, page, "uid2", name="n2", description="d2", page_text="p2", comment="c2", restriction_id="r2")
    assert updated.name == "n2"
    # delete_page
    page.location_file = None
    assert PageService.delete_page(db, page, "uid3")
    # delete_page with file
    page.location_file = "file.pdf"
    monkeypatch.setattr(PageService, "delete_file", lambda loc: True)
    assert PageService.delete_page(db, page, "uid3")
    # delete_page with error
    def fail(*a, **k): raise Exception("fail")
    monkeypatch.setattr(PageService, "delete_file", fail)
    page.location_file = "fail.pdf"
    db.rolled_back = False
    with pytest.raises(HTTPException):
        PageService.delete_page(db, page, "uid3")
    assert db.rolled_back

def test_hard_delete_orphaned_files():
    # Just returns 0 in current implementation
    assert PageService.hard_delete_orphaned_files() == 0
