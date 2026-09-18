"""Pruebas del limite de peticiones y del desafio anti-bot.

Lo que se comprueba aqui no es "que exista la libreria", sino las tres cosas
que romperian el sistema si estuvieran mal:
  - que el limite salte de verdad y con un mensaje que entienda un aprendiz,
  - que el escaner de porteria NO este limitado (limitarlo deja gente en la
    puerta del centro),
  - y que con el desafio apagado los formularios publicos sigan funcionando.
"""
import base64
import hashlib
import json

import pytest

from app.models.usuarios import Usuario
from app.utils import captcha as captcha_util
from app.utils.limitador import EXENTOS, LIMITES


def _login(client, identificador, contrasena='Segura2026'):
    return client.post('/auth/login',
                       data={'correo': identificador, 'password': contrasena},
                       headers={'X-Requested-With': 'XMLHttpRequest'})


class TestCatalogoDeLimites:
    """Un endpoint mal escrito en el catalogo es un limite que no existe.

    No falla ni avisa por si solo en produccion: simplemente el endpoint se
    queda sin proteccion. Por eso se comprueba aqui, no en un log.
    """

    def test_todos_los_endpoints_limitados_existen(self, app):
        reales = {r.endpoint for r in app.url_map.iter_rules()}
        declarados = {endpoint for endpoint, _, _ in LIMITES}
        assert declarados <= reales, f"Endpoints inexistentes: {declarados - reales}"

    def test_todos_los_endpoints_exentos_existen(self, app):
        reales = {r.endpoint for r in app.url_map.iter_rules()}
        assert set(EXENTOS) <= reales, f"Endpoints inexistentes: {set(EXENTOS) - reales}"


class TestLimiteDeLogin:
    def test_el_limite_salta_por_ip(self, client, crear_usuario, limitador_activo):
        crear_usuario(correo='ana@sena.edu.co')
        codigos = [_login(client, 'ana@sena.edu.co', 'incorrecta1').status_code
                   for _ in range(12)]
        assert 429 in codigos, "El limite de login nunca salto"

    def test_el_mensaje_json_es_entendible(self, client, crear_usuario,
                                           limitador_activo):
        crear_usuario(correo='ana@sena.edu.co')
        respuesta = None
        for _ in range(12):
            respuesta = _login(client, 'ana@sena.edu.co', 'incorrecta1')
            if respuesta.status_code == 429:
                break
        assert respuesta.status_code == 429
        cuerpo = respuesta.get_json()
        # Ni un 429 crudo ni un volcado tecnico: la lee una persona.
        assert 'demasiadas peticiones' in cuerpo['message'].lower()
        assert 'minuto' in cuerpo['message'].lower()
        assert respuesta.headers.get('Retry-After')

    def test_el_mensaje_html_es_una_pagina(self, client, crear_usuario,
                                           limitador_activo):
        crear_usuario(correo='ana@sena.edu.co')
        respuesta = None
        for _ in range(12):
            respuesta = client.post('/auth/login',
                                    data={'correo': 'ana@sena.edu.co',
                                          'password': 'incorrecta1'})
            if respuesta.status_code == 429:
                break
        assert respuesta.status_code == 429
        texto = respuesta.get_data(as_text=True)
        assert 'demasiado rápido' in texto.lower() or 'demasiadas' in texto.lower()

    def test_cada_ip_tiene_su_propio_contador(self, client, crear_usuario,
                                              limitador_activo):
        """Comprueba de paso que se lee la IP real detras del proxy.

        Si se estuviera contando la IP del proxy (Traefik/Coolify), todas las
        peticiones compartirian contador y la segunda IP ya llegaria bloqueada:
        un solo atacante dejaria sin login al centro entero.
        """
        crear_usuario(correo='ana@sena.edu.co')
        for _ in range(12):
            client.post('/auth/login',
                        data={'correo': 'ana@sena.edu.co', 'password': 'mala1'},
                        headers={'X-Requested-With': 'XMLHttpRequest',
                                 'X-Forwarded-For': '10.0.0.1'})

        otra = client.post('/auth/login',
                           data={'correo': 'ana@sena.edu.co', 'password': 'mala1'},
                           headers={'X-Requested-With': 'XMLHttpRequest',
                                    'X-Forwarded-For': '10.0.0.2'})
        assert otra.status_code != 429


class TestElEscanerNoSeLimita:
    """Si el escaner se limita, la gente se queda parada en la puerta."""

    def _celador(self, client, crear_usuario):
        celador = crear_usuario(correo='celador@sena.edu.co', cargo='Celador',
                                documento='777777')
        crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz',
                      documento='123123')
        _login(client, celador.correo)
        return celador

    def test_muchas_verificaciones_seguidas(self, client, crear_usuario,
                                            limitador_activo):
        self._celador(client, crear_usuario)
        # Muy por encima del techo general de la aplicacion (120 por minuto):
        # si el escaner no estuviera exento, aqui ya habria 429.
        codigos = {client.get('/porteria/api/verify/123123').status_code
                   for _ in range(150)}
        assert 429 not in codigos

    def test_muchos_movimientos_seguidos(self, client, crear_usuario,
                                         limitador_activo):
        self._celador(client, crear_usuario)
        aprendiz = Usuario.query.filter_by(correo='aprendiz@sena.edu.co').first()
        codigos = set()
        for _ in range(150):
            r = client.post(f'/porteria/register_movement/{aprendiz.id}/Entrada',
                            headers={'X-Requested-With': 'XMLHttpRequest'})
            codigos.add(r.status_code)
        assert 429 not in codigos


class TestLimiteDeMensajes:
    def test_el_centro_de_ayuda_se_limita(self, client, crear_usuario,
                                          limitador_activo):
        """Una auditoria envio 50 mensajes seguidos sin ninguna traba."""
        aprendiz = crear_usuario(correo='aprendiz@sena.edu.co', cargo='Aprendiz')
        _login(client, aprendiz.correo)

        codigos = []
        for _ in range(8):
            r = client.post('/usuarios/ayuda/contactar',
                            data={'asunto': 'Otro', 'detalle': 'Hola, necesito ayuda.'})
            codigos.append(r.status_code)
        assert 429 in codigos


class TestDesafioAntiBot:
    DATOS = {
        'nombre': 'Persona Nueva',
        'correo': 'nueva@sena.edu.co',
        'documento': '999888',
        'password': 'Segura2026',
        'confirm_password': 'Segura2026',
        'acepta_datos': 'si',
    }

    def _resolver(self, desafio):
        """Resuelve la prueba de trabajo como lo haria el navegador."""
        for numero in range(desafio['maxNumber'] + 1):
            calculado = hashlib.sha256(
                (desafio['salt'] + str(numero)).encode()).hexdigest()
            if calculado == desafio['challenge']:
                return base64.b64encode(json.dumps({
                    'algorithm': desafio['algorithm'],
                    'challenge': desafio['challenge'],
                    'number': numero,
                    'salt': desafio['salt'],
                    'signature': desafio['signature'],
                }).encode()).decode()
        raise AssertionError('El desafio no tiene solucion')

    def test_apagado_el_registro_sigue_funcionando(self, client, app):
        # Es la garantia de que la verificacion nunca deja a nadie sin poder
        # crear cuenta: si estorba, se apaga desde el .env y todo sigue igual.
        assert app.config['CAPTCHA_ACTIVO'] is False
        r = client.post('/auth/register', data=dict(self.DATOS),
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.get_json()['status'] == 'success'
        assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first()

    def test_apagado_la_recuperacion_sigue_funcionando(self, client, app,
                                                       crear_usuario):
        crear_usuario(correo='ana@sena.edu.co')
        r = client.post('/auth/recuperar', data={'email': 'ana@sena.edu.co'},
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.get_json()['status'] == 'success'

    def test_apagado_el_widget_no_se_pinta(self, client, app):
        texto = client.get('/auth/register').get_data(as_text=True)
        assert 'captcha_payload' not in texto

    @pytest.fixture
    def desafio_activo(self, app):
        app.config['CAPTCHA_ACTIVO'] = True
        # Espacio de busqueda pequeno: la prueba resuelve la PoW de verdad y no
        # tiene sentido gastar segundos de CPU en confirmar lo mismo.
        app.config['CAPTCHA_DIFICULTAD'] = 500
        captcha_util._usados.clear()
        yield app
        app.config['CAPTCHA_ACTIVO'] = False

    def test_encendido_sin_solucion_no_registra(self, client, desafio_activo):
        r = client.post('/auth/register', data=dict(self.DATOS),
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        assert Usuario.query.filter_by(correo='nueva@sena.edu.co').first() is None

    def test_encendido_con_solucion_si_registra(self, client, desafio_activo):
        desafio = client.get('/auth/captcha/desafio').get_json()
        datos = dict(self.DATOS)
        datos['captcha_payload'] = self._resolver(desafio)
        r = client.post('/auth/register', data=datos,
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.get_json()['status'] == 'success'

    def test_una_solucion_no_sirve_dos_veces(self, client, desafio_activo):
        """Sin esto un bot resuelve un desafio y reenvia el formulario mil veces."""
        desafio = client.get('/auth/captcha/desafio').get_json()
        solucion = self._resolver(desafio)

        primero = dict(self.DATOS, captcha_payload=solucion)
        assert client.post('/auth/register', data=primero,
                           headers={'X-Requested-With': 'XMLHttpRequest'}
                           ).get_json()['status'] == 'success'

        segundo = dict(self.DATOS, correo='otra@sena.edu.co', documento='999777',
                       captcha_payload=solucion)
        r = client.post('/auth/register', data=segundo,
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400
        assert Usuario.query.filter_by(correo='otra@sena.edu.co').first() is None

    def test_una_solucion_inventada_no_pasa(self, client, desafio_activo):
        """La firma HMAC es lo que impide fabricarse un desafio propio."""
        falso = base64.b64encode(json.dumps({
            'algorithm': 'SHA-256', 'challenge': 'a' * 64, 'number': 1,
            'salt': 'abc?expires=99999999999&', 'signature': 'b' * 64,
        }).encode()).decode()
        r = client.post('/auth/register',
                        data=dict(self.DATOS, captcha_payload=falso),
                        headers={'X-Requested-With': 'XMLHttpRequest'})
        assert r.status_code == 400

    def test_encendido_el_widget_se_pinta(self, client, desafio_activo):
        texto = client.get('/auth/register').get_data(as_text=True)
        assert 'captcha_payload' in texto
        assert 'js/captcha.js' in texto
