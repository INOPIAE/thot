"""
Work Status model
"""

import uuid
from sqlalchemy import Column, UUID, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class WorkStatus(Base):
    """
    Work status model - defines status for records/pages (not yet, running, finished)
    """

    __tablename__ = "workstatuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(255), nullable=False, index=True)
    workstatus_area_id = Column(UUID(as_uuid=True), ForeignKey("workstatus_areas.id"), nullable=False)

    # Relationships
    area = relationship("WorkStatusArea", back_populates="workstatuses")
    records = relationship("Record", back_populates="workstatus")
    pages = relationship("Page", back_populates="workstatus")

    def __repr__(self) -> str:
        return f"<WorkStatus(id={self.id}, status={self.status})>"
