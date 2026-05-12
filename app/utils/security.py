import re
from datetime import datetime, timezone, timedelta

def sanitize_html(text):
    """Elimina etiquetas HTML de un texto."""
    if not text:
        return text
    return re.sub(r'<[^>]*?>', '', str(text))

def format_identificador(identificador):
    """Estandariza el identificador (correo a minúsculas, cédula sin cambios)."""
    if not identificador:
        return identificador
    return identificador.strip().lower() if '@' in identificador else identificador.strip()

def check_security_and_verification():
    """Verifica la concurrencia de sesión y el estado de verificación de correo."""
    from flask import request, session, redirect, url_for, flash
    from flask_login import current_user, logout_user
    
    if current_user.is_authenticated:
        if request.endpoint and request.endpoint.startswith('static'):
            return

        # 1. Session Concurrency Check
        saved_token = session.get('session_token')
        if current_user.session_token and saved_token != current_user.session_token:
            logout_user()
            flash('Tu sesión fue cerrada porque se ingresó desde otro dispositivo.', 'danger')
            return redirect(url_for('auth.login'))

        # 2. Email Verification Check
        is_verified = getattr(current_user, 'correo_verificado', True)
        if not is_verified:
            allowed_endpoints = ['auth.verificar_correo', 'auth.reenviar_codigo', 'auth.logout', 'static']
            if request.endpoint and request.endpoint not in allowed_endpoints:
                return redirect(url_for('auth.verificar_correo'))

from . import get_colombia_time
