"""
Record model
"""

import uuid
from sqlalchemy import Column, UUID, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base
from .base import BaseModel


class Record(BaseModel):
    """
    Record model - main records with metadata and restrictions
    """

    __tablename__ = "records"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    signature = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    restriction_id = Column(UUID(as_uuid=True), ForeignKey("restrictions.id"), nullable=False)
    workstatus_id = Column(UUID(as_uuid=True), ForeignKey("workstatuses.id"), nullable=False)

    # Relationships
    restriction = relationship("Restriction", back_populates="records")
    workstatus = relationship("WorkStatus", back_populates="records")
    keywords_names = relationship("KeywordName", secondary="records_keywords_names", back_populates="records")
    keywords_locations = relationship("KeywordLocation", secondary="records_keywords_locations", back_populates="records")
    pages = relationship("Page", back_populates="record")

    def __repr__(self) -> str:
        return f"<Record(id={self.id}, title={self.title})>"
