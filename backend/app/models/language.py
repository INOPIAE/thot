"""
Language model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class Language(Base):
    """
    Language model - language entries for records
    """

    __tablename__ = "languages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language = Column(String(255), nullable=False, unique=True)

    # Relationships
    records = relationship("Record", secondary="records_languages", back_populates="languages")

    def __repr__(self) -> str:
        return f"<Language(id={self.id}, language={self.language})>"
