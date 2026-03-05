"""
Keyword Name model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class KeywordName(Base):
    """
    Keyword Name model - keywords searchable by name with phonetic and metaphone variations
    """

    __tablename__ = "keywords_names"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    c_search = Column(String(255), nullable=True, index=True)  # Cologne Phonetic
    dblmeta_1 = Column(String(255), nullable=True, index=True)  # Double Metaphone primary
    dblmeta_2 = Column(String(255), nullable=True, index=True)  # Double Metaphone secondary

    # Relationships
    records = relationship("Record", secondary="records_keywords_names", back_populates="keywords_names")

    def __repr__(self) -> str:
        return f"<KeywordName(id={self.id}, name={self.name})>"
