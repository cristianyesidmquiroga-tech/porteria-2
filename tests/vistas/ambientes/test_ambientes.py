from app.models.accesos import Acceso

ENTRAN = {'admin', 'coordinacion', 'subdirector'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/coordinacion/ambientes')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/coordinacion/ambientes')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_muestra_la_ficha_con_aprendices_adentro(client, entrar_como, crear_usuario, db):
    aprendiz = crear_usuario(correo='aprendiz.ficha@sena.edu.co', documento='3000000001',
                             ficha='2758291', programa='Sistemas')
    db.session.add(Acceso(punto_id=1, referencia_id=aprendiz.id,
                          tipo_referencia='Usuario', tipo='Entrada'))
    db.session.commit()
    entrar_como('coordinacion')
    assert '2758291' in client.get('/coordinacion/ambientes').get_data(as_text=True)


def test_detalle_de_una_ficha(client, entrar_como):
    entrar_como('subdirector')
    assert client.get('/coordinacion/ambientes/2758291').status_code == 200
