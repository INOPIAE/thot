"""Add user_record role

Revision ID: 008
Revises: 007
Create Date: 2026-03-08 00:00:00.000000

"""
from alembic import op
import uuid


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (id, name, description, created_on, active)
        VALUES (
            '7f8e9a2b-3c4d-5e6f-7a8b-9c0d1e2f3a4b',
            'user_record',
            'User is allowed to create and edit records',
            NOW(),
            true
        )
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name = 'user_record'")
