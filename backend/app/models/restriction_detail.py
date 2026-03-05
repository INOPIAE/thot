"""
Restriction Details model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, UUID, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship

from app.database import Base
from .base import BaseModel


class RestrictionDetail(BaseModel):
    """
    Restriction Details model - detailed restriction information with dates
    """

    __tablename__ = "restriction_details"

    restriction_id = Column(UUID(as_uuid=True), ForeignKey("restrictions.id"), nullable=False, index=True)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=True, index=True)
    date_until = Column(Date, nullable=True)  # Restriction valid until this date
    birth = Column(Date, nullable=True)  # Birth date (for privacy restrictions)
    marriage = Column(Date, nullable=True)  # Marriage date
    death = Column(Date, nullable=True)  # Death date
    comment = Column(Text, nullable=True)

    # Relationships
    restriction = relationship("Restriction", back_populates="restriction_details")
    page = relationship("Page", back_populates="restriction_details")

    def __repr__(self) -> str:
        return f"<RestrictionDetail(id={self.id}, restriction_id={self.restriction_id})>"
