"""fk foto revisada por

Revision ID: 3bad3b9e5ead
Revises: 9c6020c70856
Create Date: 2026-09-28 16:15:14.473091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bad3b9e5ead'
down_revision = '9c6020c70856'
branch_labels = None
depends_on = None


FK = 'fk_usuarios_foto_revisada_por_usuarios'


def upgrade():
    op.execute("UPDATE usuarios u SET foto_revisada_por = NULL "
               "WHERE foto_revisada_por IS NOT NULL AND NOT EXISTS "
               "(SELECT 1 FROM usuarios a WHERE a.id = u.foto_revisada_por)")
    op.execute(f"ALTER TABLE usuarios ADD CONSTRAINT {FK} "
               "FOREIGN KEY (foto_revisada_por) REFERENCES usuarios (id) "
               "ON DELETE SET NULL NOT VALID")
    op.execute(f"ALTER TABLE usuarios VALIDATE CONSTRAINT {FK}")


def downgrade():
    op.drop_constraint(FK, 'usuarios', type_='foreignkey')
