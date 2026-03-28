"""Add bibliographic tables: keywords_records, loantypes, languages, authors, publishers,
publicationtypes, record_conditions, letterings, record_authors and extend records table.

Revision ID: 012
Revises: 011
Create Date: 2026-03-26 00:00:00.000000

"""
from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # New lookup / auxiliary tables                                        #
    # ------------------------------------------------------------------ #

    # keywords_records
    op.create_table(
        'keywords_records',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False, index=True, unique=True),
        sa.Column('c_search', sa.String(255), nullable=True),
        sa.Column('dblmeta_1', sa.String(255), nullable=True),
        sa.Column('dblmeta_2', sa.String(255), nullable=True),
    )
    op.create_index('ix_keywords_records_c_search', 'keywords_records', ['c_search'])
    op.create_index('ix_keywords_records_dblmeta_1', 'keywords_records', ['dblmeta_1'])
    op.create_index('ix_keywords_records_dblmeta_2', 'keywords_records', ['dblmeta_2'])

    # records_keywords_records  (junction)
    op.create_table(
        'records_keywords_records',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('record_id', PG_UUID(as_uuid=True), sa.ForeignKey('records.id'), nullable=False, index=True),
        sa.Column('keyword_record_id', PG_UUID(as_uuid=True), sa.ForeignKey('keywords_records.id'), nullable=False, index=True),
    )

    # loantypes
    op.create_table(
        'loantypes',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('loan', sa.String(255), nullable=False),
        sa.Column('subtype', sa.String(255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
    )

    # languages
    op.create_table(
        'languages',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('language', sa.String(255), nullable=False, unique=True),
    )

    # records_languages  (junction)
    op.create_table(
        'records_languages',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('record_id', PG_UUID(as_uuid=True), sa.ForeignKey('records.id'), nullable=False, index=True),
        sa.Column('language_id', PG_UUID(as_uuid=True), sa.ForeignKey('languages.id'), nullable=False, index=True),
    )

    # now: base columns helper – used by authors, record_authors, publishers
    _base_cols = lambda: [
        sa.Column('created_by', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('last_modified_by', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
    ]

    # authortypes
    op.create_table(
        'authortypes',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('authortype', sa.String(255), nullable=False, unique=True),
    )

    # authors  (with base columns)
    op.create_table(
        'authors',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('last_name', sa.String(255), nullable=False, index=True),
        sa.Column('title', sa.String(100), nullable=True),
        *_base_cols(),
    )

    # record_authors  (with base columns)
    op.create_table(
        'record_authors',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('record_id', PG_UUID(as_uuid=True), sa.ForeignKey('records.id'), nullable=False, index=True),
        sa.Column('author_id', PG_UUID(as_uuid=True), sa.ForeignKey('authors.id'), nullable=False, index=True),
        sa.Column('authortype_id', PG_UUID(as_uuid=True), sa.ForeignKey('authortypes.id'), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
        *_base_cols(),
    )

    # publishers  (with base columns)
    op.create_table(
        'publishers',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('companyname', sa.String(255), nullable=False, index=True),
        sa.Column('town', sa.String(255), nullable=True),
        *_base_cols(),
    )

    # publicationtypes
    op.create_table(
        'publicationtypes',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('publicationtype', sa.String(255), nullable=False, unique=True),
    )

    # record_conditions
    op.create_table(
        'record_conditions',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('condition', sa.String(255), nullable=False, unique=True),
    )

    # letterings
    op.create_table(
        'letterings',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('lettering', sa.String(255), nullable=False, unique=True),
    )

    # ------------------------------------------------------------------ #
    # Extend the records table                                             #
    # ------------------------------------------------------------------ #
    op.add_column('records', sa.Column('signature2', sa.String(255), nullable=True))
    op.add_column('records', sa.Column('subtitle', sa.String(500), nullable=True))
    op.add_column('records', sa.Column('year', sa.String(50), nullable=True))
    op.add_column('records', sa.Column('isbn', sa.String(50), nullable=True))
    op.add_column('records', sa.Column('number_pages', sa.String(50), nullable=True))
    op.add_column('records', sa.Column('edition', sa.String(100), nullable=True))
    op.add_column('records', sa.Column('reihe', sa.String(255), nullable=True))
    op.add_column('records', sa.Column('volume', sa.String(100), nullable=True))
    op.add_column('records', sa.Column('jahrgang', sa.String(100), nullable=True))
    op.add_column('records', sa.Column('enter_information', sa.Text(), nullable=True))
    op.add_column('records', sa.Column('indecies', sa.Text(), nullable=True))
    op.add_column('records', sa.Column('enter_date', sa.Date(), nullable=True))
    op.add_column('records', sa.Column('sort_out_date', sa.Date(), nullable=True))
    op.add_column('records', sa.Column('bibl_nr', sa.String(100), nullable=True))
    op.add_column('records', sa.Column('record_condition_id', PG_UUID(as_uuid=True),
                                       sa.ForeignKey('record_conditions.id'), nullable=True))
    op.add_column('records', sa.Column('loantype_id', PG_UUID(as_uuid=True),
                                       sa.ForeignKey('loantypes.id'), nullable=True))
    op.add_column('records', sa.Column('lettering_id', PG_UUID(as_uuid=True),
                                       sa.ForeignKey('letterings.id'), nullable=True))
    op.add_column('records', sa.Column('publicationtype_id', PG_UUID(as_uuid=True),
                                       sa.ForeignKey('publicationtypes.id'), nullable=True))
    op.add_column('records', sa.Column('publisher_id', PG_UUID(as_uuid=True),
                                       sa.ForeignKey('publishers.id'), nullable=True))

    # ------------------------------------------------------------------ #
    # Seed data                                                            #
    # ------------------------------------------------------------------ #
    now = datetime.now(timezone.utc)

    # Seed default AuthorType entry "Blank"
    authortypes_table = sa.table(
        'authortypes',
        sa.column('id', PG_UUID(as_uuid=True)),
        sa.column('authortype', sa.String),
    )
    op.bulk_insert(authortypes_table, [
        {'id': uuid.uuid4(), 'authortype': 'Blank'},
    ])


def downgrade() -> None:
    # Remove FK columns from records first
    op.drop_column('records', 'publisher_id')
    op.drop_column('records', 'publicationtype_id')
    op.drop_column('records', 'lettering_id')
    op.drop_column('records', 'loantype_id')
    op.drop_column('records', 'record_condition_id')
    op.drop_column('records', 'bibl_nr')
    op.drop_column('records', 'sort_out_date')
    op.drop_column('records', 'enter_date')
    op.drop_column('records', 'indecies')
    op.drop_column('records', 'enter_information')
    op.drop_column('records', 'jahrgang')
    op.drop_column('records', 'volume')
    op.drop_column('records', 'reihe')
    op.drop_column('records', 'edition')
    op.drop_column('records', 'number_pages')
    op.drop_column('records', 'isbn')
    op.drop_column('records', 'year')
    op.drop_column('records', 'subtitle')
    op.drop_column('records', 'signature2')

    # Drop junction tables
    op.drop_table('records_keywords_records')
    op.drop_table('records_languages')
    op.drop_table('record_authors')

    # Drop main new tables
    op.drop_table('keywords_records')
    op.drop_table('loantypes')
    op.drop_table('languages')
    op.drop_table('authors')
    op.drop_table('authortypes')
    op.drop_table('publishers')
    op.drop_table('publicationtypes')
    op.drop_table('record_conditions')
    op.drop_table('letterings')
