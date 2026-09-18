ENTRAN = {'admin', 'instructor'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/comunicados')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/comunicados')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_enviar_sin_permiso_devuelve_403(client, entrar_como):
    entrar_como('aprendiz')
    r = client.post('/usuarios/api/enviar_comunicado',
                    json={'tipo': 'Comunicado General', 'destinatarios': [1]})
    assert r.status_code == 403


def test_enviar_sin_destinatarios_se_rechaza(client, entrar_como):
    entrar_como('instructor')
    r = client.post('/usuarios/api/enviar_comunicado',
                    json={'tipo': 'Comunicado General', 'destinatarios': []})
    assert r.status_code == 400
