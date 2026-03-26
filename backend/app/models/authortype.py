"""
AuthorType model
"""

import uuid
from sqlalchemy import Column, UUID, String
from sqlalchemy.orm import relationship

from app.database import Base


class AuthorType(Base):
    """
    AuthorType model - role of an author in relation to a record
    (e.g. Author, Editor, Translator, Blank/default)
    """

    __tablename__ = "authortypes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authortype = Column(String(255), nullable=False, unique=True)

    # Relationships
    record_authors = relationship("RecordAuthor", back_populates="authortype")

    def __repr__(self) -> str:
        return f"<AuthorType(id={self.id}, authortype={self.authortype})>"
