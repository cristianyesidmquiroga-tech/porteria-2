import pytest

CARPETAS = {'celador': ['celador', 'porteria']}


def pytest_generate_tests(metafunc):
    if 'perfil' in metafunc.fixturenames:
        carpeta = metafunc.definition.path.parent.name
        metafunc.parametrize('perfil', CARPETAS.get(carpeta, [carpeta]))


@pytest.fixture
def usuario(entrar_como, perfil):
    return entrar_como(perfil)


@pytest.fixture
def sesion(client, usuario):
    return client


@pytest.fixture
def otro_usuario(crear_usuario):
    return crear_usuario(correo='otra.persona@sena.edu.co',
                         documento='1000000099', nombre='Otra Persona')
