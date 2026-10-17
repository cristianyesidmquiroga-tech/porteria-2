import os
import subprocess
import sys

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
URL = os.environ.get('MIGRACIONES_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='sin base PostgreSQL de pruebas')

REV_ANTES_RENOMBRE = '665d70c9588d'
REV_RENOMBRE = '08ded79b3b48'


def flask_db(*args):
    entorno = {**os.environ, 'DATABASE_URL': URL,
               'FLASK_APP': 'run.py', 'EJECUTAR_TAREAS': 'false'}
    r = subprocess.run([sys.executable, '-m', 'flask', 'db', *args],
                       cwd=RAIZ, env=entorno, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def revisiones():
    script = ScriptDirectory(os.path.join(RAIZ, 'migrations'))
    return [r.revision for r in reversed(list(script.walk_revisions()))]


def test_una_sola_cabeza():
    script = ScriptDirectory(os.path.join(RAIZ, 'migrations'))
    assert len(script.get_heads()) == 1


def test_escalera_sube_y_baja_cada_revision():
    flask_db('downgrade', 'base')
    for rev in revisiones():
        flask_db('upgrade', rev)
        flask_db('downgrade', '--', '-1')
        flask_db('upgrade', rev)


def test_renombre_conserva_datos():
    flask_db('downgrade', 'base')
    flask_db('upgrade', REV_ANTES_RENOMBRE)
    motor = create_engine(URL)
    with motor.begin() as c:
        c.execute(text("insert into objetos_externos (descripcion, propietario) "
                       "values ('Portatil', 'Ana')"))
    flask_db('upgrade', REV_RENOMBRE)
    with motor.connect() as c:
        valor = c.execute(text("select nombre_propietario from objetos_externos "
                               "where descripcion = 'Portatil'")).scalar()
    assert valor == 'Ana'


def test_fk_validada():
    flask_db('upgrade', 'head')
    with create_engine(URL).connect() as c:
        validada = c.execute(text(
            "select convalidated from pg_constraint "
            "where conname = 'fk_usuarios_foto_revisada_por_usuarios'")).scalar()
    assert validada is True
