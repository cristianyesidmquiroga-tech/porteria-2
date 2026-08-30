import hmac
import re

# Longitud minima unica para todo el sistema. Antes convivian tres reglas
# distintas (0, 4 y 6 caracteres) segun el flujo por el que se cambiara.
LONGITUD_MINIMA_CONTRASENA = 8


def sanitize_html(text):
    """Elimina etiquetas HTML de un texto.

    Es una limpieza de entrada, no una defensa contra XSS: el escape correcto
    se hace al renderizar (Jinja lo hace solo; en JavaScript se usa
    textContent, nunca innerHTML con datos de la base).
    """
    if not text:
        return text
    return re.sub(r'<[^>]*?>', '', str(text))


def format_identificador(identificador):
    """Estandariza el identificador (correo a minusculas, cedula sin cambios)."""
    if not identificador:
        return identificador
    return identificador.strip().lower() if '@' in identificador else identificador.strip()


def comparar_codigo(esperado, recibido):
    """Compara dos codigos en tiempo constante.

    Una comparacion con == filtra por tiempo cuantos caracteres coinciden, lo
    que ayuda a adivinar el codigo caracter por caracter.
    """
    if not esperado or not recibido:
        return False
    return hmac.compare_digest(str(esperado), str(recibido))


def validar_contrasena(contrasena, confirmacion=None):
    """Valida una contrasena nueva. Devuelve un mensaje de error o None si es valida."""
    if not contrasena:
        return 'Debes escribir una contrasena.'
    if confirmacion is not None and contrasena != confirmacion:
        return 'Las contrasenas no coinciden.'
    if len(contrasena) < LONGITUD_MINIMA_CONTRASENA:
        return (f'La contrasena debe tener al menos '
                f'{LONGITUD_MINIMA_CONTRASENA} caracteres.')
    if contrasena.isdigit() or contrasena.isalpha():
        return 'La contrasena debe combinar letras y numeros.'
    return None


def correo_permitido(correo, dominios_permitidos):
    """Comprueba si el correo pertenece a alguno de los dominios permitidos.

    Una lista vacia significa que no hay restriccion.
    """
    if not dominios_permitidos:
        return True
    if not correo or '@' not in correo:
        return False
    dominio = correo.rsplit('@', 1)[1].lower()
    return dominio in dominios_permitidos


def check_security_and_verification():
    """Verifica la concurrencia de sesion y el estado de verificacion de correo."""
    from flask import request, redirect, url_for, flash, session
    from flask_login import current_user, logout_user

    if not current_user.is_authenticated:
        return None

    if request.endpoint and request.endpoint.startswith('static'):
        return None

    # 1. Sesion unica por usuario.
    # Antes esto solo comparaba si current_user.session_token tenia valor, asi
    # que ponerlo en NULL (lo que hacen el logout y el cambio de contrasena)
    # DESACTIVABA la comprobacion en vez de cerrar la sesion: una cookie
    # robada seguia siendo valida despues de cerrar sesion.
    saved_token = session.get('session_token')
    if not saved_token or not current_user.session_token or not comparar_codigo(
            current_user.session_token, saved_token):
        logout_user()
        session.clear()
        flash('Tu sesion fue cerrada porque se ingreso desde otro dispositivo.', 'danger')
        return redirect(url_for('auth.login'))

    # 2. Verificacion de correo
    if not getattr(current_user, 'correo_verificado', True):
        permitidos = ['auth.verificar_correo', 'auth.reenviar_codigo',
                      'auth.cambiar_password_obligatorio', 'auth.logout',
                      'main.politica_privacidad', 'main.salud', 'static']
        if request.endpoint and request.endpoint not in permitidos:
            return redirect(url_for('auth.verificar_correo'))

    return None
