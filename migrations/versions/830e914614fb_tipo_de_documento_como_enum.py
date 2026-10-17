"""tipo de documento como enum

Revision ID: 830e914614fb
Revises: 08ded79b3b48
Create Date: 2026-09-28 16:12:52.771517

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '830e914614fb'
down_revision = '08ded79b3b48'
branch_labels = None
depends_on = None

tipo = postgresql.ENUM('CC', 'TI', 'CE', 'PPT', 'PA', name='tipo_documento')


def upgrade():
    tipo.create(op.get_bind(), checkfirst=True)
    op.execute("UPDATE usuarios SET tipo_documento = 'CC' "
               "WHERE tipo_documento IS NULL "
               "OR tipo_documento NOT IN ('CC','TI','CE','PPT','PA')")
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_documento DROP DEFAULT")
    op.alter_column('usuarios', 'tipo_documento',
                    existing_type=sa.String(5), type_=tipo,
                    postgresql_using='tipo_documento::tipo_documento')
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_documento SET DEFAULT 'CC'")


def downgrade():
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_documento DROP DEFAULT")
    op.alter_column('usuarios', 'tipo_documento',
                    existing_type=tipo, type_=sa.String(5),
                    postgresql_using='tipo_documento::text')
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_documento SET DEFAULT 'CC'")
    tipo.drop(op.get_bind(), checkfirst=True)
