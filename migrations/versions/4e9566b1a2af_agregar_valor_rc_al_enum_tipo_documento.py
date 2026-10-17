"""agregar valor RC al enum tipo documento

Revision ID: 4e9566b1a2af
Revises: 830e914614fb
Create Date: 2026-09-28 16:13:31.266977

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e9566b1a2af'
down_revision = '830e914614fb'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipo_documento ADD VALUE IF NOT EXISTS 'RC'")


def downgrade():
    pass  # PostgreSQL no permite quitar un valor de un ENUM
