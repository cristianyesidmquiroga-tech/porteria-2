from app.models.mensajes import Mensaje


def test_entra_al_centro_de_ayuda(sesion):
    assert sesion.get('/usuarios/ayuda').status_code == 200


def test_contacta_a_un_asesor(sesion, usuario):
    r = sesion.post('/usuarios/ayuda/contactar',
                    data={'asunto': 'Otro', 'detalle': 'Necesito ayuda'})
    assert r.headers['Location'] == '/usuarios/mensajes'
    assert Mensaje.query.filter_by(usuario_id=usuario.id).count() == 1
