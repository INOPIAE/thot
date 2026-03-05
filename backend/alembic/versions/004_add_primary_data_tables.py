"""Add primary data tables

Revision ID: 004
Revises: 003
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create workstatus_areas table
    op.create_table(
        'workstatus_areas',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('area', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('area')
    )
    op.create_index('ix_workstatus_areas_area', 'workstatus_areas', ['area'])

    # Create workstatuses table
    op.create_table(
        'workstatuses',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(255), nullable=False),
        sa.Column('workstatus_area_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['workstatus_area_id'], ['workstatus_areas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workstatuses_status', 'workstatuses', ['status'])

    # Create restrictions table
    op.create_table(
        'restrictions',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_restrictions_name', 'restrictions', ['name'])

    # Create keywords_names table
    op.create_table(
        'keywords_names',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('c_search', sa.String(255), nullable=True),
        sa.Column('dblmeta_1', sa.String(255), nullable=True),
        sa.Column('dblmeta_2', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_keywords_names_name', 'keywords_names', ['name'])
    op.create_index('ix_keywords_names_c_search', 'keywords_names', ['c_search'])
    op.create_index('ix_keywords_names_dblmeta_1', 'keywords_names', ['dblmeta_1'])
    op.create_index('ix_keywords_names_dblmeta_2', 'keywords_names', ['dblmeta_2'])

    # Create keywords_locations table
    op.create_table(
        'keywords_locations',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('c_search', sa.String(255), nullable=True),
        sa.Column('dblmeta_1', sa.String(255), nullable=True),
        sa.Column('dblmeta_2', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_keywords_locations_name', 'keywords_locations', ['name'])
    op.create_index('ix_keywords_locations_c_search', 'keywords_locations', ['c_search'])
    op.create_index('ix_keywords_locations_dblmeta_1', 'keywords_locations', ['dblmeta_1'])
    op.create_index('ix_keywords_locations_dblmeta_2', 'keywords_locations', ['dblmeta_2'])

    # Create records table (with base columns)
    op.create_table(
        'records',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_modified_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('signature', sa.String(255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('restriction_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('workstatus_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['restriction_id'], ['restrictions.id'], ),
        sa.ForeignKeyConstraint(['workstatus_id'], ['workstatuses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_records_title', 'records', ['title'])

    # Create records_keywords_names junction table
    op.create_table(
        'records_keywords_names',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('record_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('keyword_name_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['record_id'], ['records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['keyword_name_id'], ['keywords_names.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_records_keywords_names_record_id', 'records_keywords_names', ['record_id'])
    op.create_index('ix_records_keywords_names_keyword_name_id', 'records_keywords_names', ['keyword_name_id'])

    # Create records_keywords_locations junction table
    op.create_table(
        'records_keywords_locations',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('record_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('keyword_location_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['record_id'], ['records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['keyword_location_id'], ['keywords_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_records_keywords_locations_record_id', 'records_keywords_locations', ['record_id'])
    op.create_index('ix_records_keywords_locations_keyword_location_id', 'records_keywords_locations', ['keyword_location_id'])

    # Create pages table (with base columns)
    op.create_table(
        'pages',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_modified_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('page', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('record_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('location_file', sa.String(255), nullable=True),
        sa.Column('location_thumbnail', sa.String(255), nullable=True),
        sa.Column('location_file_watermark', sa.String(255), nullable=True),
        sa.Column('restriction_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('workstatus_id', sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['record_id'], ['records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['restriction_id'], ['restrictions.id'], ),
        sa.ForeignKeyConstraint(['workstatus_id'], ['workstatuses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pages_record_id', 'pages', ['record_id'])

    # Create restriction_details table (with base columns)
    op.create_table(
        'restriction_details',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_modified_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('restriction_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('date_until', sa.Date(), nullable=True),
        sa.Column('birth', sa.Date(), nullable=True),
        sa.Column('marriage', sa.Date(), nullable=True),
        sa.Column('death', sa.Date(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['restriction_id'], ['restrictions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_restriction_details_restriction_id', 'restriction_details', ['restriction_id'])


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    op.drop_index('ix_restriction_details_restriction_id', table_name='restriction_details')
    op.drop_table('restriction_details')

    op.drop_index('ix_pages_record_id', table_name='pages')
    op.drop_table('pages')

    op.drop_index('ix_records_keywords_locations_keyword_location_id', table_name='records_keywords_locations')
    op.drop_index('ix_records_keywords_locations_record_id', table_name='records_keywords_locations')
    op.drop_table('records_keywords_locations')

    op.drop_index('ix_records_keywords_names_keyword_name_id', table_name='records_keywords_names')
    op.drop_index('ix_records_keywords_names_record_id', table_name='records_keywords_names')
    op.drop_table('records_keywords_names')

    op.drop_index('ix_records_title', table_name='records')
    op.drop_table('records')

    op.drop_index('ix_keywords_locations_dblmeta_2', table_name='keywords_locations')
    op.drop_index('ix_keywords_locations_dblmeta_1', table_name='keywords_locations')
    op.drop_index('ix_keywords_locations_c_search', table_name='keywords_locations')
    op.drop_index('ix_keywords_locations_name', table_name='keywords_locations')
    op.drop_table('keywords_locations')

    op.drop_index('ix_keywords_names_dblmeta_2', table_name='keywords_names')
    op.drop_index('ix_keywords_names_dblmeta_1', table_name='keywords_names')
    op.drop_index('ix_keywords_names_c_search', table_name='keywords_names')
    op.drop_index('ix_keywords_names_name', table_name='keywords_names')
    op.drop_table('keywords_names')

    op.drop_index('ix_restrictions_name', table_name='restrictions')
    op.drop_table('restrictions')

    op.drop_index('ix_workstatuses_status', table_name='workstatuses')
    op.drop_table('workstatuses')

    op.drop_index('ix_workstatus_areas_area', table_name='workstatus_areas')
    op.drop_table('workstatus_areas')
