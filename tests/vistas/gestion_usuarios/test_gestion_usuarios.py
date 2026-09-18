from app.models.usuarios import Rol, Usuario

ENTRAN = {'admin'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/usuarios/admin_gestion')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/'


def test_sin_sesion_pide_login(client):
    r = client.get('/usuarios/admin_gestion')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def _rol(nombre):
    return Rol.query.filter_by(nombre=nombre).first().id


def test_crea_un_usuario_con_contrasena_temporal(client, entrar_como):
    entrar_como('admin')
    client.post('/usuarios/api/admin/crear_usuario',
                json={'nombre': 'Nueva Persona', 'correo': 'Nueva@sena.edu.co',
                      'contraseña': 'Temporal2026', 'rol_id': _rol('Usuario'),
                      'cargo': 'Aprendiz'})
    nuevo = Usuario.query.filter_by(correo='nueva@sena.edu.co').first()
    assert nuevo.debe_cambiar_contrasena is True


def test_cargo_invalido_se_rechaza(client, entrar_como):
    entrar_como('admin')
    r = client.post('/usuarios/api/admin/crear_usuario',
                    json={'nombre': 'X', 'correo': 'x@sena.edu.co',
                          'contraseña': 'Temporal2026', 'rol_id': _rol('Usuario'),
                          'cargo': 'Rey'})
    assert r.status_code == 400


def test_edita_y_desbloquea(client, entrar_como, crear_usuario, db):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002',
                         intentos_fallidos=5)
    entrar_como('admin')
    client.put(f'/usuarios/api/admin/editar_usuario/{otro.id}',
               json={'nombre': 'Nombre Nuevo', 'estado_bloqueo': 'desbloquear'})
    db.session.refresh(otro)
    assert otro.nombre == 'Nombre Nuevo'
    assert otro.intentos_fallidos == 0


def test_elimina_un_usuario(client, entrar_como, crear_usuario, db):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    entrar_como('admin')
    client.delete(f'/usuarios/api/admin/eliminar_usuario/{otro.id}', json={})
    assert db.session.get(Usuario, otro.id) is None


def test_no_elimina_otro_admin(client, entrar_como, crear_usuario):
    otro = crear_usuario(correo='otro.admin@sena.edu.co', documento='3000000003',
                         rol='Admin')
    entrar_como('admin')
    r = client.delete(f'/usuarios/api/admin/eliminar_usuario/{otro.id}', json={})
    assert r.status_code == 403


def test_api_sin_permiso_devuelve_403(client, entrar_como):
    entrar_como('administrador')
    r = client.post('/usuarios/api/admin/crear_usuario', json={})
    assert r.status_code == 403
