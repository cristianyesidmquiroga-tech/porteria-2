import pytest

VISTAS = [
    pytest.param('/coordinacion/ambientes', '/usuarios/profile', id='ambientes'),
    pytest.param('/usuarios/asistencia', '/usuarios/profile', id='asistencia'),
    pytest.param('/usuarios/admin/mensajes', '/', id='bandeja_mensajes'),
    pytest.param('/usuarios/comunicados', '/usuarios/profile', id='comunicados'),
    pytest.param('/porteria/scanner', '/usuarios/profile', id='escaner'),
    pytest.param('/usuarios/admin/fichas', '/', id='fichas'),
    pytest.param('/usuarios/admin_gestion', '/', id='gestion_usuarios'),
    pytest.param('/usuarios/admin_historial', '/', id='historial_cambios'),
    pytest.param('/porteria/historial_clases', '/usuarios/profile', id='historial_clases'),
    pytest.param('/porteria/dashboard', '/usuarios/profile', id='panel'),
    pytest.param('/porteria/pases', '/usuarios/profile', id='pases'),
    pytest.param('/porteria/analytics/Aprendiz', '/porteria/dashboard', id='reportes'),
    pytest.param('/usuarios/admin/respaldos', '/', id='respaldos'),
    pytest.param('/usuarios/admin/fotos', '/', id='revision_fotos'),
]


@pytest.mark.parametrize('url,destino', VISTAS)
def test_no_entra(sesion, url, destino):
    r = sesion.get(url)
    assert r.status_code == 302
    assert r.headers['Location'] == destino


def test_no_registra_equipos(sesion):
    r = sesion.post('/equipos/add', data={'nombre': 'Portatil'},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.status_code == 400
