import os
from datetime import timedelta
from dotenv import load_dotenv

# load_dotenv() sin argumentos busca un archivo llamado ".env" desde el
# directorio actual hacia arriba, y este proyecto lo guarda en config/.env:
# nunca lo encontraba, por eso en local siempre se caia a los valores por
# defecto. Se apunta a la ruta real.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


def _requerido(nombre, ayuda):
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno obligatoria {nombre}. {ayuda}"
        )
    return valor


class Config:
    # Sin valor por defecto: una clave adivinable permite falsificar cookies de
    # sesion y suplantar al administrador.
    SECRET_KEY = _requerido(
        'SECRET_KEY',
        'Genera una con: python -c "import secrets; print(secrets.token_hex(32))"'
    )

    # Sin fallback a SQLite: un fallback silencioso escribe en el disco efimero
    # del contenedor y se pierde toda la base en cada redespliegue.
    database_url = _requerido(
        'DATABASE_URL',
        'Ejemplo: postgresql://usuario:clave@host:5432/basededatos'
    )

    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}

    SCHEDULER_API_ENABLED = False

    # --- Cookies de sesion ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Se desactiva solo para desarrollo local sin HTTPS.
    SESSION_COOKIE_SECURE = os.environ.get('COOKIES_SEGURAS', 'true').lower() != 'false'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_DURATION = timedelta(hours=12)

    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # Dominios permitidos en el registro publico. Vacio = sin restriccion.
    DOMINIOS_REGISTRO = [
        d.strip().lower()
        for d in os.environ.get('DOMINIOS_REGISTRO', '').split(',')
        if d.strip()
    ]
