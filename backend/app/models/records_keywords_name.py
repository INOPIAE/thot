"""
Records Keywords Name association model
"""

import uuid
from sqlalchemy import Column, UUID, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class RecordsKeywordsName(Base):
    """
    Junction table for many-to-many relationship between Records and Keyword Names
    """

    __tablename__ = "records_keywords_names"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False, index=True)
    keyword_name_id = Column(UUID(as_uuid=True), ForeignKey("keywords_names.id"), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<RecordsKeywordsName(record_id={self.record_id}, keyword_name_id={self.keyword_name_id})>"
