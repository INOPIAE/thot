"""Add user confirmation tables and admin flag to user registrations

Revision ID: 009
Revises: 008
Create Date: 2026-03-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_confirmation',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('confirmation', sa.String(length=255), nullable=False),
        sa.Column('confirmation_short', sa.String(length=50), nullable=False),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_modified_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_confirmation_confirmation', 'user_confirmation', ['confirmation'], unique=True)
    op.create_index('ix_user_confirmation_confirmation_short', 'user_confirmation', ['confirmation_short'], unique=True)

    op.create_table(
        'user_confirmations',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('userid', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('confirmation', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('comment', sa.String(length=1000), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_modified_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['userid'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['confirmation'], ['user_confirmation.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_confirmations_userid', 'user_confirmations', ['userid'], unique=False)
    op.create_index('ix_user_confirmations_confirmation', 'user_confirmations', ['confirmation'], unique=False)

    op.add_column(
        'user_registrations',
        sa.Column('admin', sa.Boolean(), nullable=False, server_default='false')
    )

    op.execute(
        """
        INSERT INTO user_confirmation (id, confirmation, confirmation_short, created_on, active)
        VALUES (
            '0fd8be53-8e4f-4f25-b8c9-8c00fd8f15b1',
            'Terms of Service',
            'ToS',
            NOW(),
            true
        )
        ON CONFLICT (confirmation_short) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_column('user_registrations', 'admin')

    op.drop_index('ix_user_confirmations_confirmation', table_name='user_confirmations')
    op.drop_index('ix_user_confirmations_userid', table_name='user_confirmations')
    op.drop_table('user_confirmations')

    op.drop_index('ix_user_confirmation_confirmation_short', table_name='user_confirmation')
    op.drop_index('ix_user_confirmation_confirmation', table_name='user_confirmation')
    op.drop_table('user_confirmation')
