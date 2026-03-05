"""
Page model
"""

import uuid
from sqlalchemy import Column, UUID, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base
from .base import BaseModel


class Page(BaseModel):
    """
    Page model - individual pages within records with media locations
    """

    __tablename__ = "pages"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    page = Column(Text, nullable=True)  # Page content/text
    comment = Column(Text, nullable=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False, index=True)
    location_file = Column(String(255), nullable=True)  # Path to original file
    location_thumbnail = Column(String(255), nullable=True)  # Path to thumbnail
    location_file_watermark = Column(String(255), nullable=True)  # Path to watermarked file
    restriction_id = Column(UUID(as_uuid=True), ForeignKey("restrictions.id"), nullable=False)
    workstatus_id = Column(UUID(as_uuid=True), ForeignKey("workstatuses.id"), nullable=True)

    # Relationships
    record = relationship("Record", back_populates="pages")
    restriction = relationship("Restriction", back_populates="pages")
    workstatus = relationship("WorkStatus", back_populates="pages")
    restriction_details = relationship("RestrictionDetail", back_populates="page")

    def __repr__(self) -> str:
        return f"<Page(id={self.id}, name={self.name})>"
