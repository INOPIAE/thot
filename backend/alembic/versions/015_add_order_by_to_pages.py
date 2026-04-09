"""
Revision ID: 015_add_order_by_to_pages
Revises: 014_remove_unique_email_from_users
Create Date: 2026-04-09

Add order_by column to pages table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('pages', sa.Column('order_by', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('pages', 'order_by')
