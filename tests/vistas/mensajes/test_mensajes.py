from app.models.mensajes import Mensaje

def test_todos_los_perfiles_entran(client, entrar_como, clave):
    entrar_como(clave)
    assert client.get('/usuarios/mensajes').status_code == 200


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/mensajes')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_envia_un_mensaje(client, entrar_como):
    usuario = entrar_como('aprendiz')
    client.post('/usuarios/mensajes/enviar', data={'texto': 'Hola'})
    assert Mensaje.query.filter_by(usuario_id=usuario.id).count() == 1


def test_mensaje_demasiado_largo_no_se_envia(client, entrar_como):
    usuario = entrar_como('aprendiz')
    client.post('/usuarios/mensajes/enviar', data={'texto': 'a' * 2001})
    assert Mensaje.query.filter_by(usuario_id=usuario.id).count() == 0


def test_solo_ve_sus_mensajes(client, entrar_como, crear_usuario, db):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    db.session.add(Mensaje(usuario_id=otro.id, autor_id=otro.id,
                           autor_nombre=otro.nombre, texto='Mensaje privado'))
    db.session.commit()
    entrar_como('aprendiz')
    assert 'Mensaje privado' not in client.get('/usuarios/mensajes').get_data(as_text=True)
