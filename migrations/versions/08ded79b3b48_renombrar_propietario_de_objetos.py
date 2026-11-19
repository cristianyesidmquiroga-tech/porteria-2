"""renombrar propietario de objetos

Revision ID: 08ded79b3b48
Revises: 665d70c9588d
Create Date: 2026-09-28 16:11:50.216947

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08ded79b3b48'
down_revision = '665d70c9588d'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('objetos_externos', 'propietario',
                    new_column_name='nombre_propietario')


def downgrade():
    op.alter_column('objetos_externos', 'nombre_propietario',
                    new_column_name='propietario')
