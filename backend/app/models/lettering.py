"""
Lettering model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class Lettering(Base):
    """
    Lettering model - type of lettering/script used in a record (e.g. Antiqua, Fraktur, Handschrift)
    """

    __tablename__ = "letterings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lettering = Column(String(255), nullable=False, unique=True)

    # Relationships
    records = relationship("Record", back_populates="lettering")

    def __repr__(self) -> str:
        return f"<Lettering(id={self.id}, lettering={self.lettering})>"
