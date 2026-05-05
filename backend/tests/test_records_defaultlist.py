
import pytest
import uuid
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Record, Restriction, WorkStatus, WorkStatusArea
from app.database import get_db

def create_test_record(db: Session, title="TestRecord", signature="SIG1", nlf_fdb=False, pers_count=None):
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
        workstatus_id=workstatus.id,
        nlf_fdb=nlf_fdb,
        pers_count=pers_count
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


def test_list_records_default_nlf_fdb_and_pers_count(db_session, client):
    """
    Test that nlf_fdb and pers_count are present and correct in defaultlist endpoint.
    """
    import uuid
    # Create record with default values
    title1 = f"NLF-FDB-DEFAULT-{uuid.uuid4()}"
    rec1 = create_test_record(db_session, title=title1, signature="SIG-NLF-1", nlf_fdb=False, pers_count=None)
    # Create record with nlf_fdb True and pers_count set
    title2 = f"NLF-FDB-SET-{uuid.uuid4()}"
    rec2 = create_test_record(db_session, title=title2, signature="SIG-NLF-2", nlf_fdb=True, pers_count=7)
    # Query first record
    response1 = client.get(
        "/api/v1/records/defaultlist",
        params={"title": title1},
        headers={"host": "localhost"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["items"]) == 1
    item1 = data1["items"][0]
    assert item1["title"] == title1
    assert item1["nlf_fdb"] is False
    assert item1["pers_count"] is None

    # Query second record
    response2 = client.get(
        "/api/v1/records/defaultlist",
        params={"title": title2},
        headers={"host": "localhost"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 1
    item2 = data2["items"][0]
    assert item2["title"] == title2
    assert item2["nlf_fdb"] is True
    assert item2["pers_count"] == 7

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

