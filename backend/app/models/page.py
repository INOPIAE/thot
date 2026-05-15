"""
Page model
"""

import uuid
from sqlalchemy import Column, UUID, String, ForeignKey, Text
import sqlalchemy as sa
from sqlalchemy.orm import relationship, synonym

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
    # Database column renamed to `orgin_file` (intentional spelling from requirements).
    # Keep `location_file` as ORM synonym for backward compatibility in existing code.
    orgin_file = Column(String(255), nullable=True)  # Path to original file
    location_file = synonym("orgin_file")
    current_file = Column(Text, nullable=True)
    restriction_file = Column(Text, nullable=True)
    location_thumbnail = Column(String(255), nullable=True)  # Path to thumbnail
    location_file_watermark = Column(String(255), nullable=True)  # Path to watermarked file
    restriction_id = Column(UUID(as_uuid=True), ForeignKey("restrictions.id"), nullable=False)
    workstatus_id = Column(UUID(as_uuid=True), ForeignKey("workstatuses.id"), nullable=True)
    order_by = Column(sa.Integer, nullable=True)

    rotation = Column(sa.Integer, nullable=False, default=0, server_default="0")
    rotation_restriction = Column(sa.Integer, nullable=False, default=0, server_default="0")

    # Relationships
    record = relationship("Record", back_populates="pages")
    restriction = relationship("Restriction", back_populates="pages")
    workstatus = relationship("WorkStatus", back_populates="pages")
    restriction_details = relationship("RestrictionDetail", back_populates="page")

    def __repr__(self) -> str:
        return f"<Page(id={self.id}, name={self.name})>"
