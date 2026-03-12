"""
User confirmation definition model (e.g. Terms of Service)
"""

from sqlalchemy import Column, String

from .base import BaseModel


class UserConfirmation(BaseModel):
    """
    Master table for available user confirmations
    """

    __tablename__ = "user_confirmation"

    confirmation = Column(String(255), nullable=False, unique=True, index=True)
    confirmation_short = Column(String(50), nullable=False, unique=True, index=True)

    def __repr__(self) -> str:
        return f"<UserConfirmation(id={self.id}, confirmation_short={self.confirmation_short})>"
