ENTRAN = {'admin'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/admin/fotos')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/admin/fotos')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_revisar_sin_permiso_devuelve_403(client, entrar_como, crear_usuario):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    entrar_como('administrativo')
    r = client.post(f'/usuarios/api/admin/fotos/{otro.id}/revisar',
                    json={'decision': 'aprobar'})
    assert r.status_code == 403


def test_rechazar_sin_motivo_se_rechaza(client, entrar_como, crear_usuario):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002',
                         foto='user_1.jpg', foto_estado='pendiente')
    entrar_como('admin')
    r = client.post(f'/usuarios/api/admin/fotos/{otro.id}/revisar',
                    json={'decision': 'rechazar', 'motivo': ''})
    assert r.status_code == 400


def test_aprueba_una_foto(client, entrar_como, crear_usuario, db):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002',
                         foto='user_1.jpg', foto_estado='pendiente')
    entrar_como('admin')
    client.post(f'/usuarios/api/admin/fotos/{otro.id}/revisar',
                json={'decision': 'aprobar'})
    db.session.refresh(otro)
    assert otro.foto_estado == 'aprobada'
