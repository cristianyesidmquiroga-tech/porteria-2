"""Desafío anti-bot autoalojado (prueba de trabajo), compatible con ALTCHA v1.

Por qué esto y no un servicio externo (Turnstile / reCAPTCHA):
  - No sale ni un byte hacia un tercero, así que ningún dato del aprendiz se
    entrega a una empresa ajena (Ley 1581 de 2012: minimizar el tratamiento).
  - No hay dependencia de red en el camino crítico del registro. Si Cloudflare
    o Google no responden, con Turnstile nadie puede crear cuenta; aquí no
    existe ese modo de fallo porque el desafío lo emite el mismo servidor.
  - No añade ninguna librería nueva: el protocolo son treinta líneas de
    hashlib/hmac. La librería oficial `altcha` (MIT, sin dependencias) hace
    exactamente esto, pero su widget de navegador habría que traerlo de un CDN
    o vender un bundle minificado al repositorio, que es justo lo que se
    quería evitar.

El protocolo es el de ALTCHA v1 a propósito, no uno inventado: el servidor
emite `salt` y `número`, publica `SHA-256(salt + número)` firmado con HMAC, y
el navegador tiene que encontrar el número probando desde cero. Verificar
cuesta un hash; resolver cuesta, de media, la mitad del rango. Eso vuelve caro
el registro masivo sin pedirle nada a la persona. Si algún día se quiere el
widget oficial de ALTCHA, encaja sin tocar el servidor.

Lo que NO es: una barrera contra un atacante dirigido, que puede pagar el
coste de CPU. Contra eso trabaja el límite de peticiones, no esto.
"""
import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
import urllib.parse

from flask import current_app, request

logger = logging.getLogger(__name__)

# Nombre del campo oculto que el widget rellena en el formulario.
CAMPO = 'captcha_payload'

# Vigencia del desafío. Suficiente para llenar un formulario largo con calma,
# corto como para que un desafío resuelto no se pueda revender más tarde.
VIGENCIA_SEGUNDOS = 15 * 60

MENSAJE_ERROR = ('No pudimos verificar que eres una persona. Recarga la '
                 'página y vuelve a intentarlo.')

# Desafíos ya canjeados, para que una misma solución no sirva dos veces.
# En memoria a propósito: el servidor corre con un solo worker (ver
# docker/entrypoint.sh). Con varios procesos habría que moverlo a Redis, igual
# que el almacenamiento del limitador.
_usados: dict[str, float] = {}


def captcha_activo():
    """El desafío se puede apagar entero desde el .env.

    Dejar a la gente sin poder registrarse por culpa de la verificación es peor
    que el spam que evita, así que tiene que existir un interruptor.
    """
    return bool(current_app.config.get('CAPTCHA_ACTIVO'))


def _clave_hmac():
    """Firma derivada de SECRET_KEY: no hay un secreto más que administrar."""
    semilla = current_app.config['SECRET_KEY']
    if isinstance(semilla, str):
        semilla = semilla.encode()
    return hmac.new(semilla, b'captcha-desafio', hashlib.sha256).digest()


def _firma(desafio):
    return hmac.new(_clave_hmac(), desafio.encode(), hashlib.sha256).hexdigest()


def _limpiar_usados(ahora):
    for clave, expira in list(_usados.items()):
        if expira < ahora:
            _usados.pop(clave, None)


def crear_desafio():
    """Genera un desafío nuevo, en el formato que espera el widget."""
    ahora = int(time.time())
    maximo = int(current_app.config.get('CAPTCHA_DIFICULTAD', 60000))
    numero = secrets.randbelow(maximo + 1)

    # El `expires` viaja dentro del salt y queda cubierto por la firma, así que
    # nadie puede alargar la vigencia de un desafío sin invalidarlo.
    salt = (secrets.token_hex(12) + '?'
            + urllib.parse.urlencode({'expires': ahora + VIGENCIA_SEGUNDOS})
            + '&')
    desafio = hashlib.sha256((salt + str(numero)).encode()).hexdigest()

    return {
        'algorithm': 'SHA-256',
        'challenge': desafio,
        'maxNumber': maximo,
        'salt': salt,
        'signature': _firma(desafio),
    }


def verificar(payload_b64):
    """Comprueba la solución. Devuelve (valido, mensaje_de_error)."""
    if not payload_b64:
        return False, MENSAJE_ERROR

    try:
        datos = json.loads(base64.b64decode(payload_b64))
        salt = str(datos['salt'])
        numero = int(datos['number'])
        desafio = str(datos['challenge'])
        firma = str(datos['signature'])
    except Exception:
        return False, MENSAJE_ERROR

    # 1. La firma demuestra que el desafío lo emitimos nosotros.
    if not hmac.compare_digest(firma, _firma(desafio)):
        return False, MENSAJE_ERROR

    # 2. El desafío corresponde de verdad a ese salt y ese número.
    esperado = hashlib.sha256((salt + str(numero)).encode()).hexdigest()
    if not hmac.compare_digest(esperado, desafio):
        return False, MENSAJE_ERROR

    ahora = time.time()

    # 3. Vigencia.
    try:
        parametros = dict(urllib.parse.parse_qsl(salt.split('?', 1)[1]))
        if float(parametros['expires']) < ahora:
            return False, ('La verificación de seguridad caducó. Recarga la '
                           'página e inténtalo de nuevo.')
    except (IndexError, KeyError, ValueError):
        return False, MENSAJE_ERROR

    # 4. Un desafío resuelto vale una sola vez: si no, un bot resuelve uno y
    #    reenvía el mismo formulario mil veces.
    _limpiar_usados(ahora)
    if desafio in _usados:
        return False, MENSAJE_ERROR
    _usados[desafio] = ahora + VIGENCIA_SEGUNDOS

    return True, None


def validar_formulario():
    """Valida el campo del formulario actual. Devuelve (valido, mensaje).

    Si el desafío está apagado por configuración, no estorba: devuelve válido.
    """
    if not captcha_activo():
        return True, None
    valido, mensaje = verificar(request.form.get(CAMPO))
    if not valido:
        logger.info("Desafio anti-bot rechazado en %s", request.endpoint)
    return valido, mensaje
