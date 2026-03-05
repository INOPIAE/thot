"""
Work Status Area model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class WorkStatusArea(Base):
    """
    Work status area model - defines areas for work status (record, page)
    """

    __tablename__ = "workstatus_areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area = Column(String(255), nullable=False, unique=True, index=True)

    # Relationships
    workstatuses = relationship("WorkStatus", back_populates="area", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<WorkStatusArea(id={self.id}, area={self.area})>"
