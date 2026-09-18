def test_todos_los_perfiles_entran(client, entrar_como, clave):
    entrar_como(clave)
    assert client.get('/usuarios/tutorial').status_code == 200


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/tutorial')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_marca_el_tutorial_como_visto(client, entrar_como, db):
    usuario = entrar_como('aprendiz', tutorial_visto=False)
    client.post('/usuarios/tutorial/completar')
    db.session.refresh(usuario)
    assert usuario.tutorial_visto is True
