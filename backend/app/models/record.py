"""
Record model
"""

import uuid
from sqlalchemy import Column, UUID, String, ForeignKey, Text, Date
from sqlalchemy.orm import relationship

from app.database import Base
from .base import BaseModel


class Record(BaseModel):
    """
    Record model - main records with metadata and restrictions
    """

    __tablename__ = "records"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    signature = Column(String(255), nullable=True)
    signature2 = Column(String(255), nullable=True)
    subtitle = Column(String(500), nullable=True)
    comment = Column(Text, nullable=True)
    year = Column(String(50), nullable=True)
    isbn = Column(String(50), nullable=True)
    number_pages = Column(String(50), nullable=True)
    edition = Column(String(100), nullable=True)
    reihe = Column(String(255), nullable=True)
    volume = Column(String(100), nullable=True)
    jahrgang = Column(String(100), nullable=True)
    enter_information = Column(Text, nullable=True)
    indecies = Column(Text, nullable=True)
    enter_date = Column(Date, nullable=True)
    sort_out_date = Column(Date, nullable=True)
    bibl_nr = Column(String(100), nullable=True)
    restriction_id = Column(UUID(as_uuid=True), ForeignKey("restrictions.id"), nullable=False)
    workstatus_id = Column(UUID(as_uuid=True), ForeignKey("workstatuses.id"), nullable=False)
    record_condition_id = Column(UUID(as_uuid=True), ForeignKey("record_conditions.id"), nullable=True)
    loantype_id = Column(UUID(as_uuid=True), ForeignKey("loantypes.id"), nullable=True)
    lettering_id = Column(UUID(as_uuid=True), ForeignKey("letterings.id"), nullable=True)
    publicationtype_id = Column(UUID(as_uuid=True), ForeignKey("publicationtypes.id"), nullable=True)
    publisher_id = Column(UUID(as_uuid=True), ForeignKey("publishers.id"), nullable=True)

    # Relationships
    restriction = relationship("Restriction", back_populates="records")
    workstatus = relationship("WorkStatus", back_populates="records")
    keywords_names = relationship("KeywordName", secondary="records_keywords_names", back_populates="records")
    keywords_locations = relationship("KeywordLocation", secondary="records_keywords_locations", back_populates="records")
    keywords_records = relationship("KeywordRecord", secondary="records_keywords_records", back_populates="records")
    languages = relationship("Language", secondary="records_languages", back_populates="records")
    record_authors = relationship("RecordAuthor", back_populates="record", order_by="RecordAuthor.order")
    record_condition = relationship("RecordCondition", back_populates="records")
    loantype = relationship("LoanType", back_populates="records")
    lettering = relationship("Lettering", back_populates="records")
    publicationtype = relationship("PublicationType", back_populates="records")
    publisher = relationship("Publisher", back_populates="records")
    pages = relationship("Page", back_populates="record")

    def __repr__(self) -> str:
        return f"<Record(id={self.id}, title={self.title})>"
