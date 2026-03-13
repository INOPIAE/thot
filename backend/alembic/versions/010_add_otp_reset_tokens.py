"""Add otp_reset_tokens table

Revision ID: 010
Revises: 009
Create Date: 2026-03-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'otp_reset_tokens',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('userid', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('otp_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['userid'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_otp_reset_tokens_userid', 'otp_reset_tokens', ['userid'], unique=False)
    op.create_index('ix_otp_reset_tokens_token', 'otp_reset_tokens', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_otp_reset_tokens_token', table_name='otp_reset_tokens')
    op.drop_index('ix_otp_reset_tokens_userid', table_name='otp_reset_tokens')
    op.drop_table('otp_reset_tokens')