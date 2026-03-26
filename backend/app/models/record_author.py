"""
RecordAuthor model - junction table linking Records, Authors and AuthorTypes
"""

import uuid
from sqlalchemy import Column, UUID, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import BaseModel


class RecordAuthor(BaseModel):
    """
    RecordAuthor - links a record to an author with a specific role/type and ordering.
    Equivalent to the 'Authors' table in the specification.
    """

    __tablename__ = "record_authors"

    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id"), nullable=False, index=True)
    authortype_id = Column(UUID(as_uuid=True), ForeignKey("authortypes.id"), nullable=True)
    order = Column(Integer, nullable=True, default=0)

    # Relationships
    record = relationship("Record", back_populates="record_authors")
    author = relationship("Author", back_populates="record_authors")
    authortype = relationship("AuthorType", back_populates="record_authors")

    def __repr__(self) -> str:
        return f"<RecordAuthor(record_id={self.record_id}, author_id={self.author_id})>"
