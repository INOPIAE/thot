"""
User Registration model
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, UUID, Boolean

from app.database import Base


class UserRegistration(Base):
    """
    User registration model for temporary storage of registration data
    """

    __tablename__ = "user_registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    admin = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<UserRegistration(id={self.id}, username={self.username}, email={self.email})>"

    def is_expired(self) -> bool:
        """Check if registration token has expired"""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None) if self.expires_at.tzinfo else datetime.utcnow() > self.expires_at
