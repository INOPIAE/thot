"""
Add rotation_restriction column to pages table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('pages', sa.Column('rotation_restriction', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('pages', 'rotation_restriction')