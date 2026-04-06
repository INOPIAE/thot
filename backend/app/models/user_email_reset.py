import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class UserEmailReset(Base):
    __tablename__ = "user_email_reset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="email_resets")

    def __init__(self, *args, **kwargs):
        expires_at = kwargs.get("expires_at")
        if expires_at is not None and expires_at.tzinfo is None:
            from datetime import timezone
            kwargs["expires_at"] = expires_at.replace(tzinfo=timezone.utc)
        super().__init__(*args, **kwargs)
