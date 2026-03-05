"""
Keyword Location model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class KeywordLocation(Base):
    """
    Keyword Location model - keywords for locations searchable with phonetic and metaphone variations
    """

    __tablename__ = "keywords_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    c_search = Column(String(255), nullable=True, index=True)  # Cologne Phonetic
    dblmeta_1 = Column(String(255), nullable=True, index=True)  # Double Metaphone primary
    dblmeta_2 = Column(String(255), nullable=True, index=True)  # Double Metaphone secondary

    # Relationships
    records = relationship("Record", secondary="records_keywords_locations", back_populates="keywords_locations")

    def __repr__(self) -> str:
        return f"<KeywordLocation(id={self.id}, name={self.name})>"
