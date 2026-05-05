"""
Revision ID: 017_add_notifications_table
Revises: 016_add_nlf_fdb_pers_count_to_records
Create Date: 2026-05-05

Add notifications table
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_modified_by', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('notification', sa.Text(), nullable=False),
        sa.Column('roles_id', psql.UUID(as_uuid=True), sa.ForeignKey('roles.id'), nullable=False),
    )

def downgrade():
    op.drop_table('notifications')
