ENTRAN = {'admin', 'administrador', 'administrativo'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/admin/mensajes')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/admin/mensajes')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_responder_sin_permiso_devuelve_403(client, entrar_como, crear_usuario):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    entrar_como('aprendiz')
    r = client.post(f'/usuarios/api/admin/mensajes/{otro.id}', json={'texto': 'Hola'})
    assert r.status_code == 403


def test_responder_a_quien_no_existe_devuelve_404(client, entrar_como):
    entrar_como('admin')
    r = client.post('/usuarios/api/admin/mensajes/99999', json={'texto': 'Hola'})
    assert r.status_code == 404


def test_el_documento_se_ve_enmascarado(client, entrar_como, crear_usuario):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    entrar_como('administrativo')
    html = client.get(f'/usuarios/admin/mensajes/{otro.id}').get_data(as_text=True)
    assert '3000000002' not in html
