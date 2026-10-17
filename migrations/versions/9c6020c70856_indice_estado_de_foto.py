"""indice estado de foto

Revision ID: 9c6020c70856
Revises: d342651a791b
Create Date: 2026-09-28 16:14:54.242128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c6020c70856'
down_revision = 'd342651a791b'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.create_index('ix_usuarios_foto_estado', 'usuarios', ['foto_estado'],
                        postgresql_concurrently=True, if_not_exists=True)


def downgrade():
    with op.get_context().autocommit_block():
        op.drop_index('ix_usuarios_foto_estado', table_name='usuarios',
                      postgresql_concurrently=True, if_exists=True)
