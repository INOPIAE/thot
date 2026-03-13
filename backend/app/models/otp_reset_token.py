"""
OTP reset token model
"""

import uuid

from sqlalchemy import Column, String, DateTime, UUID, Boolean, ForeignKey

from app.database import Base


class OTPResetToken(Base):
    """
    Temporary OTP reset token model for confirming a new OTP secret
    """

    __tablename__ = "otp_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userid = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    otp_token = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<OTPResetToken(id={self.id}, userid={self.userid}, used={self.used})>"