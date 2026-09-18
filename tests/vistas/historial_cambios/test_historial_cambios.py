from app.models.accesos import Auditoria

ENTRAN = {'admin'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/admin_historial')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/admin_historial')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_muestra_los_cambios_registrados(client, entrar_como, db):
    usuario = entrar_como('admin')
    db.session.add(Auditoria(usuario_id=usuario.id, nombre_usuario=usuario.nombre,
                             tabla_afectada='usuarios', registro_id=1,
                             accion='Cambio de prueba'))
    db.session.commit()
    assert 'Cambio de prueba' in client.get('/usuarios/admin_historial').get_data(as_text=True)
