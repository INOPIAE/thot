"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

from config import config

# Create database engine
# Build a SQLAlchemy URL using explicit components to correctly handle
# non-ASCII credentials. `URL.create()` will quote username/password as needed.
engine_url = URL.create(
    drivername="postgresql+psycopg2",
    username=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_NAME,
)

engine = create_engine(
    engine_url,
    echo=getattr(config, 'SQLALCHEMY_ECHO', False),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# alembic expects a metadata object
from sqlalchemy import MetaData

# Create base class for models
Base = declarative_base()

# alembic expects a metadata object
alembic_metadata = Base.metadata

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
