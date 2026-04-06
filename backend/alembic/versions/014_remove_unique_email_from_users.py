"""
Remove unique constraint from email in users table
"""
from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None

def upgrade():
    # Drop unique index on email
    op.drop_index('ix_users_email', table_name='users')
    # Recreate non-unique index
    op.create_index('ix_users_email', 'users', ['email'], unique=False)


def downgrade():
    # Drop non-unique index
    op.drop_index('ix_users_email', table_name='users')
    # Recreate unique index
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
