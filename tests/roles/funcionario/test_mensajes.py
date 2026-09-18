from app.models.mensajes import Mensaje


def test_entra_a_sus_mensajes(sesion):
    assert sesion.get('/usuarios/mensajes').status_code == 200


def test_envia_un_mensaje(sesion, usuario):
    r = sesion.post('/usuarios/mensajes/enviar', data={'texto': 'Hola'})
    assert r.headers['Location'] == '/usuarios/mensajes'
    assert Mensaje.query.filter_by(usuario_id=usuario.id).count() == 1


def test_mensaje_vacio_no_se_envia(sesion, usuario):
    sesion.post('/usuarios/mensajes/enviar', data={'texto': '   '})
    assert Mensaje.query.filter_by(usuario_id=usuario.id).count() == 0
