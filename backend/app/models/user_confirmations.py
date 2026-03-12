"""
User confirmation acceptance model
"""

from sqlalchemy import Column, String, UUID, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserConfirmations(BaseModel):
    """
    Records per-user confirmations for entries from user_confirmation
    """

    __tablename__ = "user_confirmations"

    userid = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    confirmation = Column(UUID(as_uuid=True), ForeignKey("user_confirmation.id", ondelete="RESTRICT"), nullable=False, index=True)
    comment = Column(String(1000), nullable=True)

    user = relationship("User")
    confirmation_entry = relationship("UserConfirmation")

    def __repr__(self) -> str:
        return f"<UserConfirmations(id={self.id}, userid={self.userid}, confirmation={self.confirmation})>"
