from app.models.entidades import Equipo

AJAX = {'X-Requested-With': 'XMLHttpRequest'}
NO_REGISTRAN = {'celador', 'porteria', 'trabajador'}


def test_registro_segun_el_perfil(client, entrar_como, clave):
    usuario = entrar_como(clave)
    r = client.post('/equipos/add', headers=AJAX,
                    data={'nombre': 'Portatil', 'tipo': 'Portátil'})
    registrados = Equipo.query.filter_by(usuario_id=usuario.id).count()
    if clave in NO_REGISTRAN:
        assert r.status_code == 400
        assert registrados == 0
    else:
        assert r.get_json()['status'] == 'success'
        assert registrados == 1


def test_maximo_cinco_equipos(client, entrar_como):
    usuario = entrar_como('aprendiz')
    for i in range(6):
        client.post('/equipos/add', headers=AJAX, data={'nombre': f'Equipo {i}'})
    assert Equipo.query.filter_by(usuario_id=usuario.id).count() == 5


def test_serial_repetido_se_rechaza(client, entrar_como):
    entrar_como('aprendiz')
    client.post('/equipos/add', headers=AJAX, data={'nombre': 'A', 'serial': 'SN1'})
    r = client.post('/equipos/add', headers=AJAX, data={'nombre': 'B', 'serial': 'SN1'})
    assert r.status_code == 400


def test_tipo_invalido_se_rechaza(client, entrar_como):
    entrar_como('aprendiz')
    r = client.post('/equipos/add', headers=AJAX, data={'nombre': 'A', 'tipo': 'Nevera'})
    assert r.status_code == 400


def test_no_borra_el_equipo_de_otro(client, entrar_como, crear_usuario, db):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    equipo = Equipo(nombre='Ajeno', usuario_id=otro.id)
    db.session.add(equipo)
    db.session.commit()
    entrar_como('aprendiz')
    r = client.post(f'/equipos/delete/{equipo.id}', headers=AJAX)
    assert r.status_code == 400
    assert db.session.get(Equipo, equipo.id) is not None
