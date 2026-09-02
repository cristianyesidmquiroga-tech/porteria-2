"""Límite de peticiones (rate limiting) de toda la aplicación.

Todos los límites viven en este archivo, no repartidos como decoradores por
las vistas. La razón es práctica: un límite mal puesto en un endpoint de
portería deja al centro sin poder registrar entradas, así que la lista
completa tiene que poder leerse de una sola vez para revisarla, y no depender
de que alguien recuerde buscar decoradores en veinte archivos.

Los límites se aplican envolviendo la función registrada en
`app.view_functions` después de registrar los blueprints. Es equivalente a
decorar la vista en su archivo, pero permite dejar aquí la justificación de
cada número junto a los demás.
"""
import logging
import time

from flask import current_app, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user

logger = logging.getLogger(__name__)


def clave_cliente():
    """Identifica a quien hace la petición: por usuario si hay sesión, si no por IP.

    En el SENA todo el centro puede salir a internet por una misma IP pública.
    Limitar solo por IP castigaría a los cientos de aprendices conectados al
    wifi por culpa de uno solo, así que en cuanto hay sesión el contador pasa a
    ser individual. Sin sesión no queda otra referencia que la IP.
    """
    try:
        if current_user and current_user.is_authenticated:
            return f"usuario:{current_user.id}"
    except Exception:  # pragma: no cover - fuera de contexto de login
        pass
    return f"ip:{get_remote_address()}"


def clave_ip():
    """Siempre por IP, aunque haya sesión abierta.

    Se usa en los formularios sin sesión (login, registro, recuperación): ahí
    se persigue a quien prueba credenciales en serie, no a una cuenta.
    """
    return f"ip:{get_remote_address()}"


def _clave_correo_del_formulario():
    """Cuenta por el correo escrito en el formulario, no por quien lo escribe.

    Sin esto, alguien con varias IP podría pedir cien códigos de recuperación
    del mismo correo y convertir el sistema en una máquina de inundar el buzón
    de esa persona.
    """
    correo = (request.form.get('email') or request.form.get('correo') or '').strip().lower()
    return f"correo:{correo}" if correo else clave_ip()


def _solo_post():
    """Los límites de formulario no deben gastarse al abrir la página (GET)."""
    return request.method != 'POST'


limiter = Limiter(key_func=clave_cliente)


# --- Catálogo de límites -------------------------------------------------
#
# Formato: (endpoint, [límites], {opciones})
#
# El "porqué" de cada número va en el comentario; el "qué" ya se lee solo.
LIMITES = [
    # ---- Sin sesión: se cuenta por IP ----

    # Emisión del desafío anti-bot: es barato (un hash), pero no hay motivo
    # para que una misma IP pida miles de desafíos sin llegar a usarlos.
    ('auth.captcha_desafio', ["60 per minute"], {'key_func': clave_ip}),

    # Fuerza bruta de contraseñas. El bloqueo por cuenta (5 intentos) ya existe
    # en login.py, pero solo frena el ataque contra UNA cuenta: sin este límite
    # se pueden probar 3 contraseñas comunes contra 500 cuentas distintas sin
    # llegar a bloquear ninguna.
    ('auth.login', ["10 per minute", "80 per hour"],
     {'key_func': clave_ip, 'exempt_when': _solo_post}),

    # Crea cuentas y manda correo. Una persona real se registra una vez; 5 por
    # hora deja margen de sobra para reintentos y errores de formulario.
    ('auth.register', ["5 per hour", "20 per day"],
     {'key_func': clave_ip, 'exempt_when': _solo_post}),

    # Cada petición dispara un correo saliente. Dos límites a la vez: por IP
    # (quien inunda) y por correo destino (a quién se inunda).
    ('auth.recuperar_solicitar', ["5 per hour", "15 per day"],
     {'key_func': clave_ip, 'exempt_when': _solo_post}),
    ('auth.recuperar_solicitar', ["3 per hour"],
     {'key_func': _clave_correo_del_formulario, 'exempt_when': _solo_post}),

    # Adivinar el código de 6 dígitos. Hay tope de 5 intentos por cuenta, pero
    # se reinicia al pedir un código nuevo; el límite por IP cierra ese ciclo.
    ('auth.recuperar_verificar', ["15 per hour"],
     {'key_func': clave_ip, 'exempt_when': _solo_post}),
    ('auth.recuperar_cambiar', ["10 per hour"],
     {'key_func': clave_ip, 'exempt_when': _solo_post}),

    # ---- Con sesión: se cuenta por usuario ----

    # Mismo caso que el código de recuperación, ya con sesión abierta.
    ('auth.verificar_correo', ["20 per hour"], {'exempt_when': _solo_post}),

    # Reenvío del código de verificación: un correo saliente por clic.
    ('auth.reenviar_codigo', ["3 per hour", "10 per day"], {}),

    # Subir foto cuesta entre 0,4 y 2 segundos de CPU (OpenCV) y el servidor
    # corre con UN worker y 1 CPU: repetirlo en bucle deja a portería sin
    # escáner. El mismo endpoint guarda el resto del perfil, así que el margen
    # es holgado para quien solo viene a corregir sus datos.
    ('usuarios.update_profile', ["6 per minute", "40 per hour"], {}),

    # Mensajería: una auditoría envió 50 mensajes seguidos por el centro de
    # ayuda sin ninguna traba. Escribir a un asesor se hace un par de veces al
    # día, no cincuenta por minuto.
    ('usuarios.enviar_mensaje', ["5 per minute", "40 per hour"], {}),
    ('usuarios.contactar_asesor', ["5 per hour", "15 per day"], {}),

    # Exportaciones e importación: construyen un Excel entero en memoria, que
    # con un solo worker bloquea al resto de la aplicación mientras dura.
    ('porteria.export_dashboard', ["10 per hour"], {}),
    ('usuarios.api_importar_usuarios_excel', ["5 per hour"], {}),
    ('usuarios.descargar_respaldo', ["20 per hour"], {}),

    # Consulta de historial: varias consultas pesadas por llamada. La version
    # HTML ejecuta exactamente la misma consulta que la de datos, y antes solo
    # caia bajo el techo general de la aplicacion; se le pone el mismo limite.
    ('porteria.api_historial_persona', ["60 per minute"], {}),
    ('porteria.historial_persona', ["60 per minute"], {}),

    # Registro de equipos: escribe en base de datos desde un formulario.
    ('equipos.add_device', ["20 per hour"], {}),
]


# Endpoints que NUNCA se limitan. El celador escanea documentos uno detrás de
# otro en hora pico; limitarlo es dejar a la gente parada en la puerta.
EXENTOS = [
    'porteria.scanner',
    'porteria.api_verify',
    'porteria.verify',
    'porteria.register_movement',
    'porteria.register_movement_entidad',
    'porteria.register_incidente',
    # El chequeo de salud lo llama la plataforma de despliegue: si se limita,
    # Coolify puede dar el contenedor por caído y reiniciarlo en bucle.
    'main.salud',
]


def _es_peticion_json():
    """Mismo criterio que el manejador de CSRF de app/__init__.py."""
    return (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.accept_mimetypes.best == 'application/json')


def _segundos_de_espera():
    """Segundos que faltan para poder reintentar, según el limitador."""
    try:
        limite = limiter.current_limit
        if limite is not None:
            return max(int(limite.reset_at - time.time()), 1)
    except Exception:  # pragma: no cover - nunca debe tumbar la respuesta
        pass
    return 60


def registrar_manejador_429(app):
    """Respuesta legible al superar un límite.

    La lee un aprendiz desde el celular, no un desarrollador mirando logs: un
    429 crudo del servidor no le dice qué hacer ni cuándo reintentar.
    """
    @app.errorhandler(429)
    def demasiadas_peticiones(error):
        espera = _segundos_de_espera()
        if espera <= 90:
            cuanto = 'un minuto'
        elif espera < 3600:
            cuanto = f'{round(espera / 60)} minutos'
        elif espera < 5400:
            cuanto = 'una hora'
        else:
            cuanto = f'{round(espera / 3600)} horas'
        mensaje = ('Hiciste demasiadas peticiones seguidas. Espera '
                   f'{cuanto} y vuelve a intentarlo.')

        logger.warning("Limite de peticiones superado en %s", request.endpoint)

        if _es_peticion_json():
            respuesta = jsonify({"status": "error", "message": mensaje})
        else:
            respuesta = current_app.make_response(
                render_template('errores/429.html', mensaje=mensaje))
        respuesta.status_code = 429
        respuesta.headers['Retry-After'] = str(espera)
        return respuesta


def aplicar_limites(app):
    """Aplica el catálogo sobre las vistas ya registradas."""
    for endpoint in EXENTOS:
        vista = app.view_functions.get(endpoint)
        if vista is None:
            logger.warning("Endpoint exento inexistente: %s", endpoint)
            continue
        limiter.exempt(vista)

    for endpoint, limites, opciones in LIMITES:
        vista = app.view_functions.get(endpoint)
        if vista is None:
            logger.warning("Endpoint limitado inexistente: %s", endpoint)
            continue
        # Se reemplaza la vista por la versión envuelta: equivale exactamente a
        # haber escrito el decorador encima de la función en su propio archivo.
        app.view_functions[endpoint] = limiter.limit(
            ";".join(limites), **opciones)(vista)
