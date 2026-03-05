"""Add restrictions workstatus defaults and page_id to restriction_details

Revision ID: 005
Revises: 004
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

# Generate fixed UUIDs for default values
NONE_RESTRICTION_UUID = uuid.UUID('00000000-0000-0000-0000-000000000001')
RECORD_AREA_UUID = uuid.UUID('00000000-0000-0000-0000-000000000002')


def upgrade() -> None:
    # Insert workstatus areas
    op.execute(f"""
        INSERT INTO workstatus_areas (id, area) 
        VALUES ('{RECORD_AREA_UUID}', 'record')
        ON CONFLICT (area) DO NOTHING
    """)
    
    # Insert workstatuses for record area
    op.execute(f"""
        INSERT INTO workstatuses (id, status, workstatus_area_id) 
        VALUES 
            ('{uuid.uuid4()}', 'not yet', '{RECORD_AREA_UUID}'),
            ('{uuid.uuid4()}', 'running', '{RECORD_AREA_UUID}'),
            ('{uuid.uuid4()}', 'finished', '{RECORD_AREA_UUID}')
        ON CONFLICT DO NOTHING
    """)
    
    # Insert restrictions
    op.execute(f"""
        INSERT INTO restrictions (id, name) 
        VALUES 
            ('{NONE_RESTRICTION_UUID}', 'none'),
            ('{uuid.uuid4()}', 'confidential'),
            ('{uuid.uuid4()}', 'locked'),
            ('{uuid.uuid4()}', 'privacy')
        ON CONFLICT (name) DO NOTHING
    """)
    
    # Add page_id column to restriction_details table
    op.add_column('restriction_details', 
        sa.Column('page_id', sa.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_restriction_details_page_id',
        'restriction_details', 'pages',
        ['page_id'], ['id']
    )
    op.create_index('ix_restriction_details_page_id', 'restriction_details', ['page_id'])
    
    # Set default value for restriction_id in pages table
    op.alter_column('pages', 'restriction_id',
        server_default=sa.text(f"'{NONE_RESTRICTION_UUID}'"),
        existing_type=sa.UUID(as_uuid=True),
        existing_nullable=False
    )
    
    # Set default value for restriction_id in records table
    op.alter_column('records', 'restriction_id',
        server_default=sa.text(f"'{NONE_RESTRICTION_UUID}'"),
        existing_type=sa.UUID(as_uuid=True),
        existing_nullable=False
    )


def downgrade() -> None:
    # Remove default values
    op.alter_column('records', 'restriction_id',
        server_default=None,
        existing_type=sa.UUID(as_uuid=True),
        existing_nullable=False
    )
    
    op.alter_column('pages', 'restriction_id',
        server_default=None,
        existing_type=sa.UUID(as_uuid=True),
        existing_nullable=False
    )
    
    # Remove page_id column from restriction_details
    op.drop_index('ix_restriction_details_page_id', table_name='restriction_details')
    op.drop_constraint('fk_restriction_details_page_id', 'restriction_details', type_='foreignkey')
    op.drop_column('restriction_details', 'page_id')
    
    # Delete inserted data (workstatuses, restrictions, workstatus_areas)
    op.execute("DELETE FROM workstatuses WHERE workstatus_area_id IN (SELECT id FROM workstatus_areas WHERE area = 'record')")
    op.execute("DELETE FROM workstatus_areas WHERE area = 'record'")
    op.execute("DELETE FROM restrictions WHERE name IN ('none', 'confidential', 'locked', 'privacy')")
