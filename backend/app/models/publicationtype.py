"""
PublicationType model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class PublicationType(Base):
    """
    PublicationType model - type/category of a publication (e.g. Buch, Zeitschrift, etc.)
    """

    __tablename__ = "publicationtypes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicationtype = Column(String(255), nullable=False, unique=True)

    # Relationships
    records = relationship("Record", back_populates="publicationtype")

    def __repr__(self) -> str:
        return f"<PublicationType(id={self.id}, publicationtype={self.publicationtype})>"
