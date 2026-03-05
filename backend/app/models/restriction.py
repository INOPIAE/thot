"""
Restriction model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class Restriction(Base):
    """
    Restriction model - defines access restrictions (none, confidential, locked, privacy)
    """

    __tablename__ = "restrictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)

    # Relationships
    records = relationship("Record", back_populates="restriction")
    pages = relationship("Page", back_populates="restriction")
    restriction_details = relationship("RestrictionDetail", back_populates="restriction")

    def __repr__(self) -> str:
        return f"<Restriction(id={self.id}, name={self.name})>"
