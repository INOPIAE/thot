"""
Keyword Record model - bibliographic keywords with phonetic search support
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class KeywordRecord(Base):
    """
    Keyword Record model - bibliographic keywords (Schlagwörter) for records,
    searchable with Cologne Phonetic and Double Metaphone.
    """

    __tablename__ = "keywords_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True, unique=True)
    c_search = Column(String(255), nullable=True, index=True)   # Cologne Phonetic
    dblmeta_1 = Column(String(255), nullable=True, index=True)  # Double Metaphone primary
    dblmeta_2 = Column(String(255), nullable=True, index=True)  # Double Metaphone secondary

    # Relationships
    records = relationship("Record", secondary="records_keywords_records", back_populates="keywords_records")

    def __repr__(self) -> str:
        return f"<KeywordRecord(id={self.id}, name={self.name})>"
