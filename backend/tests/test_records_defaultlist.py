
import pytest
import uuid
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Record, Restriction, WorkStatus, WorkStatusArea
from app.database import get_db

def create_test_record(db: Session, title="TestRecord", signature="SIG1"):
    restriction = db.query(Restriction).first()
    if not restriction:
        restriction = Restriction(id=uuid.uuid4(), name="TestRestriction")
        db.add(restriction)
        db.commit()
        db.refresh(restriction)

    workstatus_area = db.query(WorkStatusArea).first()
    if not workstatus_area:
        workstatus_area = WorkStatusArea(id=uuid.uuid4(), area="TestArea")
        db.add(workstatus_area)
        db.commit()
        db.refresh(workstatus_area)

    workstatus = db.query(WorkStatus).first()
    if not workstatus:
        workstatus = WorkStatus(id=uuid.uuid4(), status="TestStatus", workstatus_area_id=workstatus_area.id)
        db.add(workstatus)
        db.commit()
        db.refresh(workstatus)

    record = Record(
        title=title,
        signature=signature,
        active=True,
        restriction_id=restriction.id,
        workstatus_id=workstatus.id
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@pytest.fixture
def db_session():
    db = next(get_db())
    yield db
    db.rollback()
    db.close()

@pytest.fixture(params=[True, False])
def client(request):
    os.environ["PUBLIC_USE"] = "true" if request.param else "false"
    from app.main import app
    return TestClient(app)

def test_list_records_default_empty(db_session, client):
    response = client.get("/api/v1/records/defaultlist", headers={"host": "localhost"})
    if response.status_code != 200:
        print("Response status:", response.status_code)
        print("Response text:", response.text)
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)

def test_list_records_default_with_record(db_session, client):
    import uuid
    unique_title = f"Alpha-TEST-UNIQUE-{uuid.uuid4()}"
    rec = create_test_record(db_session, title=unique_title, signature="SIGA")
    # Suche gezielt nach dem Testdatensatz über den Titel-Filter
    response = client.get(
        "/api/v1/records/defaultlist",
        params={"title": unique_title},
        headers={"host": "localhost"}
    )
    if response.status_code != 200:
        print("Response status:", response.status_code)
        print("Response text:", response.text)
    assert response.status_code == 200
    data = response.json()
    # Es sollte genau ein Eintrag mit diesem Titel zurückkommen
    matching = [item for item in data["items"] if item["title"] == unique_title]
    if not matching:
        print("rec.id:", rec.id)
        print("unique_title:", unique_title)
        print("Alle Items:")
        for item in data["items"]:
            print(item)
    assert len(matching) == 1
    assert matching[0]["id"] == str(rec.id)

def test_list_records_filter_by_title(db_session, client):
    unique_title = "Bravo-TEST-UNIQUE"
    rec = create_test_record(db_session, title=unique_title, signature="SIGB")
    response = client.get(f"/api/v1/records/defaultlist?title={unique_title}", headers={"host": "localhost"})
    if response.status_code != 200:
        print("Response status:", response.status_code)
        print("Response text:", response.text)
    assert response.status_code == 200
    data = response.json()

    assert any(item["title"] == unique_title for item in data["items"])
    assert all(unique_title in item["title"] for item in data["items"])

