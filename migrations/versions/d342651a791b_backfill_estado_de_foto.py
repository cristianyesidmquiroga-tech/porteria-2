"""backfill estado de foto

Revision ID: d342651a791b
Revises: 4e9566b1a2af
Create Date: 2026-09-28 16:14:05.947944

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd342651a791b'
down_revision = '4e9566b1a2af'
branch_labels = None
depends_on = None


def upgrade():
    conexion = op.get_bind()
    conexion.execute(sa.text("SET LOCAL lock_timeout = '3s'"))
    while True:
        filas = conexion.execute(sa.text(
            "UPDATE usuarios SET foto_estado = 'sin_foto' "
            "WHERE id IN (SELECT id FROM usuarios WHERE foto_estado IS NULL "
            "LIMIT 500 FOR UPDATE SKIP LOCKED)")).rowcount
        if filas == 0:
            break


def downgrade():
    pass
