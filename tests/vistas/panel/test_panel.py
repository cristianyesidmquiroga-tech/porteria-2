ENTRAN = {'admin', 'administrador', 'celador', 'porteria'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/porteria/dashboard')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/porteria/dashboard')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_exportar_sin_fechas_no_descarga(client, entrar_como):
    entrar_como('admin')
    r = client.get('/porteria/export_dashboard')
    assert r.status_code == 302


def test_exportar_con_fechas_descarga_csv(client, entrar_como):
    entrar_como('celador')
    r = client.get('/porteria/export_dashboard?fecha_inicio=2026-01-01&fecha_fin=2026-12-31')
    assert r.mimetype == 'text/csv'


def test_exportar_sin_permiso_no_descarga(client, entrar_como):
    entrar_como('aprendiz')
    r = client.get('/porteria/export_dashboard?fecha_inicio=2026-01-01&fecha_fin=2026-12-31')
    assert r.headers['Location'] == '/usuarios/profile'
