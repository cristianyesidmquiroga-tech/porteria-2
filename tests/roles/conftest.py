import pytest

CONTRASENA = 'Segura2026'

PERFILES = {
    'admin': [
        {'rol': 'Admin', 'cargo': 'Administrador', 'correo': 'admin@sena.edu.co',
         'documento': '1000000001', 'nombre': 'Admin de Prueba'},
    ],
    'administrador': [
        {'rol': 'Usuario', 'cargo': 'Administrador',
         'correo': 'administrador@sena.edu.co', 'documento': '1000000002',
         'nombre': 'Administrador de Prueba'},
    ],
    'administrativo': [
        {'rol': 'Usuario', 'cargo': 'Administrativo',
         'correo': 'administrativo@sena.edu.co', 'documento': '1000000003',
         'nombre': 'Administrativo de Prueba'},
    ],
    'aprendiz': [
        {'rol': 'Usuario', 'cargo': 'Aprendiz', 'correo': 'aprendiz@sena.edu.co',
         'documento': '1000000004', 'nombre': 'Aprendiz de Prueba'},
    ],
    'celador': [
        {'rol': 'Usuario', 'cargo': 'Celador', 'correo': 'celador@sena.edu.co',
         'documento': '1000000005', 'nombre': 'Celador de Prueba'},
        {'rol': 'Usuario', 'cargo': 'Portería', 'correo': 'porteria@sena.edu.co',
         'documento': '1000000006', 'nombre': 'Porteria de Prueba'},
    ],
    'contratista': [
        {'rol': 'Usuario', 'cargo': 'Contratista',
         'correo': 'contratista@sena.edu.co', 'documento': '1000000007',
         'nombre': 'Contratista de Prueba'},
    ],
    'coordinacion': [
        {'rol': 'Usuario', 'cargo': 'Coordinacion',
         'correo': 'coordinacion@sena.edu.co', 'documento': '1000000008',
         'nombre': 'Coordinacion de Prueba'},
    ],
    'funcionario': [
        {'rol': 'Usuario', 'cargo': 'Funcionario',
         'correo': 'funcionario@sena.edu.co', 'documento': '1000000009',
         'nombre': 'Funcionario de Prueba'},
    ],
    'instructor': [
        {'rol': 'Usuario', 'cargo': 'Instructor',
         'correo': 'instructor@sena.edu.co', 'documento': '1000000010',
         'nombre': 'Instructor de Prueba'},
    ],
    'subdirector': [
        {'rol': 'Usuario', 'cargo': 'Subdirector',
         'correo': 'subdirector@sena.edu.co', 'documento': '1000000011',
         'nombre': 'Subdirector de Prueba'},
    ],
    'trabajador': [
        {'rol': 'Trabajador', 'cargo': 'Funcionario',
         'correo': 'trabajador@sena.edu.co', 'documento': '1000000012',
         'nombre': 'Trabajador de Prueba'},
    ],
}


def pytest_generate_tests(metafunc):
    if 'perfil' in metafunc.fixturenames:
        perfiles = PERFILES[metafunc.definition.path.parent.name]
        metafunc.parametrize('perfil', perfiles,
                             ids=[p['cargo'] for p in perfiles])


@pytest.fixture
def usuario(app, db, perfil, crear_usuario):
    from app.models.usuarios import Rol
    if not Rol.query.filter_by(nombre=perfil['rol']).first():
        db.session.add(Rol(nombre=perfil['rol']))
        db.session.commit()
    return crear_usuario(correo=perfil['correo'], contrasena=CONTRASENA,
                         cargo=perfil['cargo'], rol=perfil['rol'],
                         documento=perfil['documento'], nombre=perfil['nombre'],
                         tutorial_visto=True)


@pytest.fixture
def sesion(client, usuario):
    r = client.post('/auth/login',
                    data={'correo': usuario.correo, 'password': CONTRASENA},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.get_json()['status'] == 'success'
    return client


@pytest.fixture
def otro_usuario(crear_usuario):
    return crear_usuario(correo='otra.persona@sena.edu.co',
                         documento='1000000099', nombre='Otra Persona')
