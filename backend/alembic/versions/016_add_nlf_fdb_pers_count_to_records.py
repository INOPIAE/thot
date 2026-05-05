"""
Add nlf_fdb and pers_count columns to records table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
table_name = 'records'

def upgrade():
    op.add_column(table_name, sa.Column('nlf_fdb', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(table_name, sa.Column('pers_count', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column(table_name, 'pers_count')
    op.drop_column(table_name, 'nlf_fdb')
