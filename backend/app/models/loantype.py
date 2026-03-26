"""
LoanType model
"""

import uuid
from sqlalchemy import Column, UUID, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class LoanType(Base):
    """
    LoanType model - defines the loan/lending type of a record (e.g. Ausleihbar, Präsenz, etc.)
    """

    __tablename__ = "loantypes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan = Column(String(255), nullable=False)
    subtype = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)

    # Relationships
    records = relationship("Record", back_populates="loantype")

    def __repr__(self) -> str:
        return f"<LoanType(id={self.id}, loan={self.loan})>"
