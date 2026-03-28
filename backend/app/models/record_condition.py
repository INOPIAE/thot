"""
RecordCondition model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class RecordCondition(Base):
    """
    RecordCondition model - physical condition of a record/book
    """

    __tablename__ = "record_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condition = Column(String(255), nullable=False, unique=True)

    # Relationships
    records = relationship("Record", back_populates="record_condition")

    def __repr__(self) -> str:
        return f"<RecordCondition(id={self.id}, condition={self.condition})>"
