"""
Author model
"""

from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class Author(BaseModel):
    """
    Author model - persons who authored records
    """

    __tablename__ = "authors"

    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=False, index=True)
    title = Column(String(100), nullable=True)  # e.g. Dr., Prof.

    # Relationships
    record_authors = relationship("RecordAuthor", back_populates="author")

    def __repr__(self) -> str:
        return f"<Author(id={self.id}, last_name={self.last_name})>"
