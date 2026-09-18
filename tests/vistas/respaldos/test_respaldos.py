ENTRAN = {'admin'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/admin/respaldos')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/admin/respaldos')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_descargar_sin_permiso_no_descarga(client, entrar_como):
    entrar_como('administrador')
    r = client.get('/usuarios/admin/descargar_respaldo/respaldo.xlsx')
    assert r.headers['Location'] == '/'


def test_no_descarga_fuera_de_la_carpeta(client, entrar_como):
    entrar_como('admin')
    r = client.get('/usuarios/admin/descargar_respaldo/..%2F..%2Fconfig.py')
    assert r.status_code == 404
