from app.models.entidades import ObjetoExterno, Visitante

ENTRAN = {'admin', 'administrador', 'celador', 'porteria'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/porteria/pases')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/porteria/pases')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_visitante_sin_documento_no_se_crea(client, entrar_como):
    entrar_como('celador')
    client.post('/porteria/pases/crear_visitante', data={'nombre': 'Sin Doc'})
    assert Visitante.query.count() == 0


def test_crea_y_desactiva_un_objeto(client, entrar_como):
    entrar_como('celador')
    client.post('/porteria/pases/crear_objeto',
                data={'descripcion': 'Taladro', 'serial': 'TAL-1'})
    objeto = ObjetoExterno.query.filter_by(serial='TAL-1').first()
    client.post(f'/porteria/pases/eliminar_objeto/{objeto.id}')
    assert ObjetoExterno.query.filter_by(serial='TAL-1').first().activo is False


def test_crear_sin_permiso_devuelve_403(client, entrar_como):
    entrar_como('aprendiz')
    r = client.post('/porteria/pases/crear_visitante',
                    data={'nombre': 'X', 'documento': '1'})
    assert r.status_code == 403
