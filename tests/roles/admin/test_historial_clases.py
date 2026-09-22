def test_entra_al_historial_de_clases(sesion):
    assert sesion.get('/porteria/historial_clases').status_code == 200


def test_busca_una_ficha(sesion):
    r = sesion.post('/porteria/historial_clases', data={'ficha': '2758291'})
    assert r.status_code == 200
