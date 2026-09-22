from app.models.mensajes import Mensaje

def test_todos_los_perfiles_entran(client, entrar_como, clave):
    entrar_como(clave)
    assert client.get('/usuarios/ayuda').status_code == 200


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/ayuda')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_contacto_con_asunto_llega_a_mensajes(client, entrar_como):
    usuario = entrar_como('aprendiz')
    client.post('/usuarios/ayuda/contactar',
                data={'asunto': 'Problema con mi foto de perfil', 'detalle': 'No carga'})
    mensaje = Mensaje.query.filter_by(usuario_id=usuario.id).first()
    assert mensaje.texto.startswith('[Problema con mi foto de perfil]')


def test_contacto_vacio_no_se_envia(client, entrar_como):
    usuario = entrar_como('aprendiz')
    client.post('/usuarios/ayuda/contactar', data={'asunto': 'Otro', 'detalle': ''})
    assert Mensaje.query.filter_by(usuario_id=usuario.id).count() == 0
