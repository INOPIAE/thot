"""
Publisher model
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import BaseModel


class Publisher(BaseModel):
    """
    Publisher model - publishing companies and their towns
    """

    __tablename__ = "publishers"

    companyname = Column(String(255), nullable=False, index=True)
    town = Column(String(255), nullable=True)

    # Relationships
    records = relationship("Record", back_populates="publisher")

    def __repr__(self) -> str:
        return f"<Publisher(id={self.id}, companyname={self.companyname})>"
