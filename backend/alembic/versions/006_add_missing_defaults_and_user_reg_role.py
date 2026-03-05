"""Add missing default entries and user_reg role

Revision ID: 006
Revises: 005
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import uuid


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO restrictions (id, name)
        VALUES
            ('00000000-0000-0000-0000-000000000001', 'none'),
            ('6b5a8858-d4f5-4c80-8f30-f3035f9b98f7', 'confidential'),
            ('f6adf357-7936-49e8-ad27-bec5133e6ba1', 'locked'),
            ('6f18fc35-8196-47f5-b4fa-d11d96ce58e3', 'privacy')
        ON CONFLICT (name) DO NOTHING
    """)

    op.execute(f"""
        INSERT INTO workstatuses (id, status, workstatus_area_id)
        SELECT '{uuid.uuid4()}', 'not yet', area.id
        FROM workstatus_areas area
        WHERE area.area = 'record'
          AND NOT EXISTS (
              SELECT 1
              FROM workstatuses ws
              WHERE ws.status = 'not yet'
                AND ws.workstatus_area_id = area.id
          )
    """)

    op.execute(f"""
        INSERT INTO workstatuses (id, status, workstatus_area_id)
        SELECT '{uuid.uuid4()}', 'running', area.id
        FROM workstatus_areas area
        WHERE area.area = 'record'
          AND NOT EXISTS (
              SELECT 1
              FROM workstatuses ws
              WHERE ws.status = 'running'
                AND ws.workstatus_area_id = area.id
          )
    """)

    op.execute(f"""
        INSERT INTO workstatuses (id, status, workstatus_area_id)
        SELECT '{uuid.uuid4()}', 'finished', area.id
        FROM workstatus_areas area
        WHERE area.area = 'record'
          AND NOT EXISTS (
              SELECT 1
              FROM workstatuses ws
              WHERE ws.status = 'finished'
                AND ws.workstatus_area_id = area.id
          )
    """)

    op.execute("""
        INSERT INTO roles (id, name, description, created_on, active)
        VALUES (
            '0c7a5455-b364-45aa-b6be-bcedab64a09f',
            'user_reg',
            'User role during registration process',
            NOW(),
            true
        )
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name = 'user_reg'")
    op.execute("DELETE FROM workstatuses WHERE status IN ('not yet', 'running', 'finished') AND workstatus_area_id IN (SELECT id FROM workstatus_areas WHERE area = 'record')")
    op.execute("DELETE FROM restrictions WHERE name IN ('none', 'confidential', 'locked', 'privacy')")
