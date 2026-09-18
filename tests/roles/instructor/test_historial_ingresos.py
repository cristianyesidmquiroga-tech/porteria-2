def test_entra_a_su_historial(sesion):
    assert sesion.get('/porteria/historial-persona').status_code == 200


def test_consulta_su_propio_historial(sesion, usuario):
    r = sesion.get(f'/porteria/api/historial-persona?usuario_id={usuario.id}')
    assert r.status_code == 200


def test_consulta_el_historial_de_otra_persona(sesion, otro_usuario):
    r = sesion.get(f'/porteria/api/historial-persona?usuario_id={otro_usuario.id}')
    assert r.status_code == 200
