def test_cierra_sesion(sesion):
    r = sesion.get('/auth/logout')
    assert r.headers['Location'] == '/auth/login'


def test_despues_de_salir_no_entra_al_perfil(sesion):
    sesion.get('/auth/logout')
    r = sesion.get('/usuarios/profile')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']
