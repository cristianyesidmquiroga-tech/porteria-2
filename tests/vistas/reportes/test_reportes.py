import pytest

ENTRAN = {'admin', 'administrador', 'celador', 'porteria'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/porteria/analytics/Aprendiz')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/porteria/dashboard'


def test_sin_sesion_pide_login(client):
    r = client.get('/porteria/analytics/Aprendiz')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


@pytest.mark.parametrize('cargo', ['Aprendiz', 'Instructor', 'Personal'])
def test_cada_reporte_abre(client, entrar_como, cargo):
    entrar_como('admin')
    assert client.get(f'/porteria/analytics/{cargo}').status_code == 200
