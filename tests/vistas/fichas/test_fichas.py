from app.models.fichas import Ficha

ENTRAN = {'admin'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/admin/fichas')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/admin/fichas')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_crea_edita_y_archiva(client, entrar_como):
    entrar_como('admin')
    client.post('/usuarios/admin/fichas/crear',
                data={'numero': '2758291', 'programa': 'Sistemas'})
    ficha = Ficha.query.filter_by(numero='2758291').first()
    client.post(f'/usuarios/admin/fichas/{ficha.id}/editar',
                data={'numero': '2758291', 'programa': 'Software'})
    client.post(f'/usuarios/admin/fichas/{ficha.id}/archivar')
    ficha = Ficha.query.filter_by(numero='2758291').first()
    assert ficha.programa == 'Software'
    assert ficha.activa is False


def test_numero_invalido_no_se_crea(client, entrar_como):
    entrar_como('admin')
    client.post('/usuarios/admin/fichas/crear', data={'numero': 'ABC', 'programa': 'X'})
    assert Ficha.query.count() == 0


def test_ficha_repetida_no_se_duplica(client, entrar_como):
    entrar_como('admin')
    for _ in range(2):
        client.post('/usuarios/admin/fichas/crear',
                    data={'numero': '2758291', 'programa': 'Sistemas'})
    assert Ficha.query.filter_by(numero='2758291').count() == 1
