import pytest

from app.models.usuarios import CARGOS_VALIDOS

DASHBOARD = '/porteria/dashboard'
PERFIL = '/usuarios/profile'
CAMBIO_OBLIGATORIO = '/auth/cambiar_password_obligatorio'
VERIFICAR_CORREO = '/auth/verificar'

CONTRASENA = 'Segura2026'

CARGOS_DE_PORTERIA = ('Celador', 'Portería', 'Administrador')

USUARIOS = [
    pytest.param('Usuario', cargo,
                 DASHBOARD if cargo in CARGOS_DE_PORTERIA else PERFIL,
                 id=cargo)
    for cargo in CARGOS_VALIDOS
] + [pytest.param('Admin', 'Administrador', DASHBOARD, id='rol-Admin')]


def _login(client, identificador, contrasena, ajax=True):
    headers = {'X-Requested-With': 'XMLHttpRequest'} if ajax else {}
    return client.post('/auth/login',
                       data={'correo': identificador, 'password': contrasena},
                       headers=headers)


def test_cubre_todos_los_cargos():
    cargos = {p.values[1] for p in USUARIOS if p.values[0] == 'Usuario'}
    assert cargos == set(CARGOS_VALIDOS)


@pytest.mark.parametrize('rol,cargo,destino', USUARIOS)
class TestLoginPorUsuario:
    def test_entra_con_correo(self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        r = _login(client, 'persona@sena.edu.co', CONTRASENA)
        assert r.status_code == 200
        assert r.get_json() == {'status': 'success', 'redirect': destino}

    def test_entra_con_documento(self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(documento='1098765432', rol=rol, cargo=cargo)
        r = _login(client, '1098765432', CONTRASENA)
        assert r.get_json()['redirect'] == destino

    def test_correo_sin_importar_mayusculas_ni_espacios(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        r = _login(client, '  Persona@SENA.edu.co ', CONTRASENA)
        assert r.get_json()['status'] == 'success'

    def test_formulario_sin_ajax_redirige(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        r = _login(client, 'persona@sena.edu.co', CONTRASENA, ajax=False)
        assert r.status_code == 302
        assert r.headers['Location'].endswith(destino)

    def test_la_pagina_de_destino_abre(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        _login(client, 'persona@sena.edu.co', CONTRASENA)
        assert client.get(destino).status_code == 200

    def test_ya_autenticado_no_vuelve_a_ver_el_login(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        _login(client, 'persona@sena.edu.co', CONTRASENA)
        r = client.get('/auth/login')
        assert r.status_code == 302
        assert r.headers['Location'].endswith('/')

    def test_contrasena_incorrecta_no_entra(
            self, client, crear_usuario, db, rol, cargo, destino):
        usuario = crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        r = _login(client, 'persona@sena.edu.co', 'Incorrecta2026')
        assert r.status_code == 401
        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 1
        assert client.get(destino).status_code != 200

    def test_bloqueo_tras_cinco_intentos(
            self, client, crear_usuario, db, rol, cargo, destino):
        usuario = crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo)
        for _ in range(5):
            _login(client, 'persona@sena.edu.co', 'Incorrecta2026')
        db.session.refresh(usuario)
        assert usuario.bloqueado_hasta is not None
        r = _login(client, 'persona@sena.edu.co', CONTRASENA)
        assert r.status_code == 403
        assert r.get_json()['bloqueado_segundos'] > 0

    def test_contrasena_temporal_obliga_a_cambiarla(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo,
                      debe_cambiar_contrasena=True, correo_verificado=False,
                      perfil_completo=False)
        r = _login(client, 'persona@sena.edu.co', CONTRASENA)
        assert r.get_json()['redirect'] == CAMBIO_OBLIGATORIO

    def test_correo_sin_verificar_va_a_verificacion(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo,
                      correo_verificado=False, perfil_completo=False)
        r = _login(client, 'persona@sena.edu.co', CONTRASENA)
        assert r.get_json()['redirect'] == VERIFICAR_CORREO

    def test_perfil_incompleto_va_al_perfil(
            self, client, crear_usuario, rol, cargo, destino):
        crear_usuario(correo='persona@sena.edu.co', rol=rol, cargo=cargo,
                      perfil_completo=False)
        r = _login(client, 'persona@sena.edu.co', CONTRASENA)
        assert r.get_json()['redirect'] == PERFIL


class TestLoginGeneral:
    def test_no_revela_si_la_cuenta_existe(self, client, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co', contrasena=CONTRASENA)
        existente = _login(client, 'ana@sena.edu.co', 'ContrasenaMala1')
        inexistente = _login(client, 'nadie@sena.edu.co', 'ContrasenaMala1')
        assert existente.get_json()['message'] == inexistente.get_json()['message']
        assert existente.status_code == inexistente.status_code

    def test_el_contador_se_reinicia_al_acertar(self, client, crear_usuario, db):
        usuario = crear_usuario(correo='ana@sena.edu.co', contrasena=CONTRASENA)
        for _ in range(3):
            _login(client, 'ana@sena.edu.co', 'incorrecta1')
        _login(client, 'ana@sena.edu.co', CONTRASENA)
        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 0

    @pytest.mark.parametrize('identificador,contrasena', [
        ('ana@sena.edu.co', ''),
        ('', CONTRASENA),
        ('', ''),
    ], ids=['sin-contrasena', 'sin-identificador', 'vacio'])
    def test_campos_vacios_no_entran(self, client, crear_usuario,
                                     identificador, contrasena):
        crear_usuario(correo='ana@sena.edu.co', contrasena=CONTRASENA)
        assert _login(client, identificador, contrasena).status_code == 401

    def test_la_pagina_de_login_abre(self, client):
        assert client.get('/auth/login').status_code == 200
