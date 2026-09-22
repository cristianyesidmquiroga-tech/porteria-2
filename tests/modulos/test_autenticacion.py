"""Pruebas de los flujos de autenticacion, bloqueo y recuperacion."""
from datetime import timedelta

from app.models.usuarios import Usuario
from app.utils import get_colombia_time


def _login(client, identificador, contrasena):
    return client.post('/auth/login',
                       data={'correo': identificador, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestLogin:
    def test_credenciales_correctas(self, client, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co', contrasena='Segura2026')
        r = _login(client, 'ana@sena.edu.co', 'Segura2026')
        assert r.status_code == 200
        assert r.get_json()['status'] == 'success'

    def test_no_revela_si_la_cuenta_existe(self, client, crear_usuario):
        # El mensaje debe ser identico exista o no la cuenta; si difiriera,
        # cualquiera podria enumerar los correos y cedulas registrados.
        crear_usuario(correo='ana@sena.edu.co', contrasena='Segura2026')
        existente = _login(client, 'ana@sena.edu.co', 'ContrasenaMala1')
        inexistente = _login(client, 'nadie@sena.edu.co', 'ContrasenaMala1')
        assert existente.get_json()['message'] == inexistente.get_json()['message']
        assert existente.status_code == inexistente.status_code

    def test_bloquea_tras_cinco_intentos(self, client, crear_usuario, db):
        usuario = crear_usuario(correo='ana@sena.edu.co', contrasena='Segura2026')
        for _ in range(5):
            _login(client, 'ana@sena.edu.co', 'incorrecta1')
        db.session.refresh(usuario)
        assert usuario.bloqueado_hasta is not None

        # Con la cuenta bloqueada, ni la contrasena correcta debe entrar.
        r = _login(client, 'ana@sena.edu.co', 'Segura2026')
        assert r.status_code == 403

    def test_el_contador_se_reinicia_al_acertar(self, client, crear_usuario, db):
        usuario = crear_usuario(correo='ana@sena.edu.co', contrasena='Segura2026')
        for _ in range(3):
            _login(client, 'ana@sena.edu.co', 'incorrecta1')
        _login(client, 'ana@sena.edu.co', 'Segura2026')
        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 0

    def test_login_sin_contrasena_no_entra(self, client, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co', contrasena='Segura2026')
        r = client.post('/auth/login', data={'correo': 'ana@sena.edu.co', 'password': ''},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 401


class TestRecuperacion:
    def _pedir_codigo(self, client, correo):
        return client.post('/auth/recuperar', data={'email': correo},
                           follow_redirects=False)

    def test_respuesta_identica_exista_o_no_la_cuenta(self, client, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co')
        con = self._pedir_codigo(client, 'ana@sena.edu.co')
        sin = self._pedir_codigo(client, 'fantasma@sena.edu.co')
        assert con.status_code == sin.status_code
        assert con.headers.get('Location') == sin.headers.get('Location')

    def test_codigo_incorrecto_se_anula_tras_cinco_intentos(
            self, client, crear_usuario, db):
        # Un codigo de 6 digitos sin limite de intentos se puede probar hasta
        # acertar y tomar la cuenta.
        usuario = crear_usuario(correo='ana@sena.edu.co')
        self._pedir_codigo(client, 'ana@sena.edu.co')

        for _ in range(5):
            client.post('/auth/recuperar/verificar', data={'codigo': '000000'})

        db.session.refresh(usuario)
        assert usuario.codigo_recuperacion is None, 'el codigo debio anularse'
        # Pero el login NO debe quedar bloqueado: si fallar codigos desde un
        # endpoint publico bloqueara la cuenta, cualquiera podria dejar al
        # celador de turno fuera del sistema de forma indefinida.
        assert usuario.bloqueado_hasta is None, 'recuperacion no debe bloquear el login'

    def test_pedir_codigo_no_reinicia_el_bloqueo_del_login(
            self, client, crear_usuario, db):
        # Los contadores de login y de codigo deben ser independientes. Si
        # compartieran contador, bastaria pedir un codigo de recuperacion entre
        # tandas de intentos para probar contrasenas sin limite.
        usuario = crear_usuario(correo='ana@sena.edu.co', contrasena='Segura2026')
        for _ in range(4):
            _login(client, 'ana@sena.edu.co', 'incorrecta1')
        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 4

        self._pedir_codigo(client, 'ana@sena.edu.co')

        db.session.refresh(usuario)
        assert usuario.intentos_fallidos == 4, 'el contador del login no debe reiniciarse'

        _login(client, 'ana@sena.edu.co', 'incorrecta1')
        db.session.refresh(usuario)
        assert usuario.bloqueado_hasta is not None, 'el quinto intento debe bloquear'

    def test_no_se_puede_saltar_al_paso_de_cambio(self, client, crear_usuario):
        crear_usuario(correo='ana@sena.edu.co')
        self._pedir_codigo(client, 'ana@sena.edu.co')
        # Sin haber verificado el codigo, el paso 3 debe rechazar el cambio.
        r = client.post('/auth/recuperar/cambiar',
                        data={'password': 'NuevaClave2026',
                              'confirm_password': 'NuevaClave2026'},
                        follow_redirects=False)
        assert r.status_code == 302
        assert '/auth/recuperar' in r.headers['Location']

    def test_codigo_expirado_se_rechaza(self, client, crear_usuario, db):
        usuario = crear_usuario(correo='ana@sena.edu.co')
        self._pedir_codigo(client, 'ana@sena.edu.co')
        db.session.refresh(usuario)
        codigo = usuario.codigo_recuperacion
        usuario.recuperacion_expiracion = get_colombia_time() - timedelta(minutes=1)
        db.session.commit()

        r = client.post('/auth/recuperar/verificar', data={'codigo': codigo},
                        follow_redirects=False)
        assert r.status_code == 302
        db.session.refresh(usuario)
        assert usuario.codigo_recuperacion is None


class TestRegistro:
    def _registrar(self, client, **campos):
        datos = {
            'nombre': 'Persona Nueva',
            'correo': 'nueva@sena.edu.co',
            'documento': '999888',
            'password': 'Segura2026',
            'confirm_password': 'Segura2026',
            'acepta_datos': 'si',
        }
        datos.update(campos)
        return client.post('/auth/register', data=datos,
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    def test_registro_valido_crea_la_cuenta(self, client):
        r = self._registrar(client)
        assert r.get_json()['status'] == 'success'
        assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is not None

    def test_sin_autorizacion_de_datos_no_se_registra(self, client):
        # Ley 1581 de 2012: sin autorizacion expresa no se pueden tratar los
        # datos personales.
        r = self._registrar(client, acepta_datos='')
        assert r.status_code == 400
        assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is None

    def test_contrasena_vacia_rechazada(self, client):
        r = self._registrar(client, password='', confirm_password='')
        assert r.status_code == 400
        assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is None

    def test_contrasena_corta_rechazada(self, client):
        r = self._registrar(client, password='abc1', confirm_password='abc1')
        assert r.status_code == 400

    def test_restriccion_de_dominio(self, client, app):
        app.config['DOMINIOS_REGISTRO'] = ['sena.edu.co']
        r = self._registrar(client, correo='alguien@gmail.com')
        assert r.status_code == 400
        assert Usuario.query.filter_by(correo='alguien@gmail.com').first() is None
