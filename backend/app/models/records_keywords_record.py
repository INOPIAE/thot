"""
Records Keywords Record association model
"""

import uuid
from sqlalchemy import Column, UUID, ForeignKey

from app.database import Base


class RecordsKeywordsRecord(Base):
    """
    Junction table for many-to-many relationship between Records and Keyword Records (bibliographic keywords)
    """

    __tablename__ = "records_keywords_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False, index=True)
    keyword_record_id = Column(UUID(as_uuid=True), ForeignKey("keywords_records.id"), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<RecordsKeywordsRecord(record_id={self.record_id}, keyword_record_id={self.keyword_record_id})>"
