"""
Database initialization and seeding
"""
# Add backend root to sys.path so \pp\ package is importable when running
# this script directly (e.g. \python scripts/init_db.py\).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.database import SessionLocal, engine
from app.models import Role, Permission
from config import config
from datetime import datetime
import uuid
import logging
from alembic.config import Config
from alembic import command
from alembic.migration import MigrationContext
from alembic.operations import Operations

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_database():
    """Initialize the database using Alembic migrations"""
    logger.info(f"Connecting to database: postgresql://{config.DB_USER}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    
    try:
        # Get path to alembic.ini
        backend_root = Path(__file__).resolve().parent.parent
        alembic_ini = backend_root / "alembic.ini"
        
        if not alembic_ini.exists():
            logger.error(f"✗ alembic.ini not found at {alembic_ini}")
            raise FileNotFoundError(f"alembic.ini not found at {alembic_ini}")
        
        # Setup Alembic config
        alembic_config = Config(str(alembic_ini))
        
        # Run migrations
        logger.info("Running Alembic migrations...")
        command.upgrade(alembic_config, "head")
        logger.info("✓ Database tables created successfully via Alembic")
        
    except OperationalError as e:
        logger.error(f"✗ Database connection failed: {e}")
        logger.error("\nTroubleshooting:")
        logger.error(f"  - Check if PostgreSQL is running on {config.DB_HOST}:{config.DB_PORT}")
        logger.error(f"  - Verify user '{config.DB_USER}' exists and password is correct")
        logger.error(f"  - Verify database '{config.DB_NAME}' exists")
        raise
    except SQLAlchemyError as e:
        logger.error(f"✗ Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Alembic error: {e}")
        raise


def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()

    try:
        # Create default roles
        roles_data = [
            {
                "name": "admin",
                "description": "Administrator with full access"
            },
            {
                "name": "support",
                "description": "Support staff for user management"
            },
            {
                "name": "user",
                "description": "Regular user with basic access"
            },
            {
                "name": "user_reg",
                "description": "User role during registration process"
            },
            {
                "name": "user_scan",
                "description": "User is allowed to create pages"
            },
            {
                "name": "user_page",
                "description": "User is allowed to change page entries"
            },
            {
                "name": "user_record",
                "description": "User is allowed to create and edit records"
            }
        ]

        for role_data in roles_data:
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing_role:
                role = Role(
                    id=uuid.uuid4(),
                    name=role_data["name"],
                    description=role_data["description"],
                    active=True,
                    created_on=datetime.utcnow()
                )
                db.add(role)
                logger.info(f"Created role: {role_data['name']}")

        # Create default permissions
        permissions_data = [
            {"name": "user:read", "description": "Read user information"},
            {"name": "user:write", "description": "Write/Update user information"},
            {"name": "user:delete", "description": "Delete user account"},
            {"name": "admin:read", "description": "Read admin information"},
            {"name": "admin:write", "description": "Write admin information"},
            {"name": "support:manage_users", "description": "Manage users as support"},
            {"name": "support:manage_roles", "description": "Manage roles as support"},
            {"name": "support:view_logs", "description": "View system logs"},
        ]

        for perm_data in permissions_data:
            existing_perm = db.query(Permission).filter(
                Permission.name == perm_data["name"]
            ).first()
            if not existing_perm:
                permission = Permission(
                    id=uuid.uuid4(),
                    name=perm_data["name"],
                    description=perm_data["description"],
                    active=True,
                    created_on=datetime.utcnow()
                )
                db.add(permission)
                logger.info(f"Created permission: {perm_data['name']}")

        db.commit()
        logger.info("✓ Database seeding completed successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error seeding database: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting database initialization...")
    logger.info("=" * 60)
    init_database()
    seed_database()
    logger.info("=" * 60)
    logger.info("✓ Database initialization completed!")
    logger.info("=" * 60)
