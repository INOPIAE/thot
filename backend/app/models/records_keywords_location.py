"""
Records Keywords Location association model
"""

import uuid
from sqlalchemy import Column, UUID, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class RecordsKeywordsLocation(Base):
    """
    Junction table for many-to-many relationship between Records and Keyword Locations
    """

    __tablename__ = "records_keywords_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False, index=True)
    keyword_location_id = Column(UUID(as_uuid=True), ForeignKey("keywords_locations.id"), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<RecordsKeywordsLocation(record_id={self.record_id}, keyword_location_id={self.keyword_location_id})>"
