from app.models.accesos import Acceso

ENTRAN = {'admin', 'administrador', 'celador', 'porteria'}


def test_acceso_segun_el_perfil(client, entrar_como, clave):
    entrar_como(clave)
    r = client.get('/porteria/scanner')
    if clave in ENTRAN:
        assert r.status_code == 200
    else:
        assert r.status_code == 302
        assert r.headers['Location'] == '/usuarios/profile'


def test_sin_sesion_pide_login(client):
    r = client.get('/porteria/scanner')
    assert r.status_code == 302
    assert '/auth/login' in r.headers['Location']


def test_documento_inexistente_no_se_encuentra(client, entrar_como):
    entrar_como('celador')
    assert client.get('/porteria/api/verify/999').get_json()['found'] is False


def test_verificar_sin_permiso_devuelve_403(client, entrar_como):
    entrar_como('aprendiz')
    assert client.get('/porteria/api/verify/123').status_code == 403


def test_registra_entrada_y_salida(client, entrar_como, crear_usuario):
    otro = crear_usuario(correo='otra.persona@sena.edu.co', documento='3000000002')
    entrar_como('porteria')
    ajax = {'X-Requested-With': 'XMLHttpRequest'}
    client.post(f'/porteria/register_movement/{otro.id}/Entrada', headers=ajax)
    client.post(f'/porteria/register_movement/{otro.id}/Salida', headers=ajax)
    tipos = [a.tipo for a in Acceso.query.filter_by(referencia_id=otro.id)
             .order_by(Acceso.id)]
    assert tipos == ['Entrada', 'Salida']


def test_registra_un_incidente(client, entrar_como):
    entrar_como('celador')
    r = client.post('/porteria/register_incidente',
                    data={'tipo_entidad': 'Usuario', 'detalles': 'Equipo sin registrar'})
    assert r.headers['Location'] == '/porteria/scanner'
