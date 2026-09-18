def test_entra_a_la_bandeja(sesion):
    assert sesion.get('/usuarios/admin/mensajes').status_code == 200


def test_abre_la_conversacion_de_otra_persona(sesion, otro_usuario):
    assert sesion.get(f'/usuarios/admin/mensajes/{otro_usuario.id}').status_code == 200


def test_responde_a_otra_persona(sesion, otro_usuario):
    r = sesion.post(f'/usuarios/api/admin/mensajes/{otro_usuario.id}',
                    json={'texto': 'Hola, ya revisamos tu caso'})
    assert r.get_json()['status'] == 'success'
