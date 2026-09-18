def test_todos_los_perfiles_cierran_sesion(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/auth/logout')
    assert r.headers['Location'] == '/auth/login'
    assert client.get('/usuarios/profile').status_code == 302


def test_borra_el_token_de_sesion(client, entrar_como, db):
    usuario = entrar_como('aprendiz')
    client.get('/auth/logout')
    db.session.refresh(usuario)
    assert usuario.session_token is None


def test_sin_sesion_pide_login(client):
    r = client.get('/auth/logout')
    assert '/auth/login' in r.headers['Location']
