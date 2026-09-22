from app.models.usuarios import Rol, Usuario


def test_entra_a_gestion_de_usuarios(sesion):
    assert sesion.get('/usuarios/admin_gestion').status_code == 200


def test_crea_un_usuario(sesion):
    rol = Rol.query.filter_by(nombre='Usuario').first()
    r = sesion.post('/usuarios/api/admin/crear_usuario',
                    json={'nombre': 'Nueva Persona', 'correo': 'nueva@sena.edu.co',
                          'contraseña': 'Temporal2026', 'rol_id': rol.id,
                          'cargo': 'Aprendiz'})
    assert r.get_json()['status'] == 'success'
    assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is not None


def test_no_puede_eliminarse_a_si_mismo(sesion, usuario):
    r = sesion.delete(f'/usuarios/api/admin/eliminar_usuario/{usuario.id}', json={})
    assert r.status_code == 400
