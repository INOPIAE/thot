"""
Records Languages association model
"""

import uuid
from sqlalchemy import Column, UUID, ForeignKey

from app.database import Base


class RecordsLanguage(Base):
    """
    Junction table for many-to-many relationship between Records and Languages
    """

    __tablename__ = "records_languages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False, index=True)
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<RecordsLanguage(record_id={self.record_id}, language_id={self.language_id})>"
