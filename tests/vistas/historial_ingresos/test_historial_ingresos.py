TERCEROS = {'admin', 'administrador', 'celador', 'instructor', 'porteria'}

def test_todos_los_perfiles_entran(client, entrar_como, clave):
    entrar_como(clave)
    assert client.get('/porteria/historial-persona').status_code == 200


def test_sin_sesion_pide_login(client):
    r = client.get('/porteria/historial-persona')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_historial_de_otra_persona_segun_el_perfil(client, entrar_como, crear_usuario, clave):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    entrar_como(clave)
    r = client.get(f'/porteria/api/historial-persona?usuario_id={otro.id}')
    assert r.status_code == (200 if clave in TERCEROS else 403)


def test_su_propio_historial(client, entrar_como):
    usuario = entrar_como('aprendiz')
    r = client.get(f'/porteria/api/historial-persona?usuario_id={usuario.id}')
    assert r.get_json()['estado'] == 'ok'
