import os
import sys

# Las variables deben existir ANTES de importar la app: config.Config las exige
# al importarse y aborta el arranque si faltan.
os.environ.setdefault('SECRET_KEY', 'clave-solo-para-pruebas-0123456789abcdef')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('COOKIES_SEGURAS', 'false')
# El planificador no debe arrancar durante las pruebas.
os.environ.setdefault('EJECUTAR_TAREAS', 'false')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest  # noqa: E402

from app import create_app, db as _db  # noqa: E402
from app.models.usuarios import Rol, Usuario  # noqa: E402
from app.models.accesos import PuntoAcceso  # noqa: E402


@pytest.fixture
def app():
    aplicacion = create_app()
    aplicacion.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
    )
    with aplicacion.app_context():
        _db.drop_all()
        _db.create_all()
        _db.session.add_all([
            Rol(nombre='Admin'),
            Rol(nombre='Usuario'),
            PuntoAcceso(id=1, nombre='Porteria Principal', tipo='General'),
        ])
        _db.session.commit()
        yield aplicacion
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def crear_usuario(app):
    def _crear(correo='aprendiz@sena.edu.co', contrasena='Segura2026',
               cargo='Aprendiz', rol='Usuario', documento='123456',
               **extras):
        rol_obj = Rol.query.filter_by(nombre=rol).first()
        usuario = Usuario(
            nombre=extras.pop('nombre', 'Persona de Prueba'),
            correo=correo,
            documento=documento,
            rol_id=rol_obj.id,
            cargo=cargo,
            correo_verificado=extras.pop('correo_verificado', True),
            perfil_completo=extras.pop('perfil_completo', True),
            **extras,
        )
        usuario.set_password(contrasena)
        _db.session.add(usuario)
        _db.session.commit()
        return usuario
    return _crear
