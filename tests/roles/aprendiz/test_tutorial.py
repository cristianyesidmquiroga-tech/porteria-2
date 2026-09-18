def test_entra_al_tutorial(sesion):
    assert sesion.get('/usuarios/tutorial').status_code == 200


def test_marca_el_tutorial_como_visto(sesion):
    r = sesion.post('/usuarios/tutorial/completar')
    assert r.get_json()['status'] == 'success'
