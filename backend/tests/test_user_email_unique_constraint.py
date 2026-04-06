import pytest
from app.models import User
from uuid import uuid4
from datetime import datetime, timezone

def create_user(db, username, email):
    user = User(
        id=uuid4(),
        username=username,
        email=email,
        hashed_password="$2b$12$1234567890123456789012abcdefghijklmno12345678901234567890",
        active=True,
        created_on=datetime.now(timezone.utc),
        current_language="de",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_duplicate_email_allowed(db):
    user1 = create_user(db, "user1", "duplicate@example.com")
    user2 = create_user(db, "user2", "duplicate@example.com")
    assert user1.email == user2.email
    assert user1.username != user2.username
    db.delete(user1)
    db.delete(user2)
    db.commit()

def test_duplicate_username_not_allowed(db):
    user1 = create_user(db, "uniqueuser", "unique1@example.com")
    with pytest.raises(Exception):
        create_user(db, "uniqueuser", "unique2@example.com")
    db.rollback()
    db.delete(user1)
    db.commit()
