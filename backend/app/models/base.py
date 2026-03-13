"""
Base model with common columns
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import Column, UUID, DateTime, Boolean, String
from sqlalchemy.orm import declared_attr

from app.database import Base


class BaseModel(Base):
    """
    Base model with common columns for all tables marked with *
    """

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_on = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_modified_by = Column(UUID(as_uuid=True), nullable=True)
    last_modified_on = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
