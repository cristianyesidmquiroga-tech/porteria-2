def test_entra_a_asistencia(sesion):
    assert sesion.get('/usuarios/asistencia').status_code == 200


def test_busca_una_ficha(sesion):
    r = sesion.post('/usuarios/asistencia',
                    data={'action': 'buscar', 'ficha': '2758291'})
    assert r.status_code == 200
