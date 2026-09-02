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

    # Zona horaria del planificador, explicita y no heredada del sistema. Hoy
    # el contenedor fija TZ en el Dockerfile y por eso "dia 1 a las 00:00"
    # coincide con la medianoche colombiana, pero eso es una casualidad de la
    # imagen: si TZ se pierde, APScheduler cae en UTC y esa misma expresion
    # pasa a dispararse el ultimo dia del mes anterior a las 19:00 hora local,
    # partiendo el mes en dos dentro del respaldo. Se fija aqui para que no
    # dependa del entorno.
    SCHEDULER_TIMEZONE = os.environ.get('ZONA_HORARIA', 'America/Bogota')

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

    # Donde se guardan las fotos de perfil. Tiene que apuntar a un directorio
    # persistente del servidor: si queda dentro del contenedor, el siguiente
    # redespliegue borra todas las fotos y no hay copia (el respaldo mensual
    # solo exporta accesos y asistencias). Sin la variable cae en la carpeta de
    # instancia, que sirve para desarrollo pero NO para produccion.
    CARPETA_FOTOS = os.environ.get('CARPETA_FOTOS') or None

    # Solo para desarrollo: recarga las plantillas al editarlas. En produccion
    # se deja apagado, que es mas rapido, porque cada despliegue reconstruye
    # el contenedor de todas formas.
    TEMPLATES_AUTO_RELOAD = os.environ.get('RECARGAR_PLANTILLAS', 'false').lower() == 'true'

    # Dominios permitidos en el registro publico. Vacio = sin restriccion.
    DOMINIOS_REGISTRO = [
        d.strip().lower()
        for d in os.environ.get('DOMINIOS_REGISTRO', '').split(',')
        if d.strip()
    ]

    # --- Limite de peticiones (rate limiting) ---

    # Numero de proxies propios delante de la aplicacion. En produccion, tras
    # Coolify/Traefik, es 1. Debe ser 0 cuando la aplicacion se expone directa
    # (desarrollo local): con un valor mayor que el real, cualquiera puede
    # falsear su IP mandando una cabecera X-Forwarded-For a mano y saltarse
    # todos los limites por IP.
    PROXIES_CONFIABLES = int(os.environ.get('PROXIES_CONFIABLES', '1'))

    # Donde se llevan los contadores. 'memory://' funciona porque el servidor
    # corre con UN solo worker de gunicorn (ver docker/entrypoint.sh), pero los
    # contadores se pierden en cada reinicio o redespliegue. Si algun dia hay
    # mas de un proceso, hay que apuntar esto a Redis (redis://host:6379/0) o
    # cada worker contara por su cuenta y el limite real sera el doble.
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Interruptor general. Se apaga solo para depurar o si un limite mal
    # calibrado estuviera bloqueando a gente real.
    RATELIMIT_ENABLED = os.environ.get('LIMITE_PETICIONES', 'true').lower() != 'false'

    # Techo general por usuario (o por IP si no hay sesion) para toda la
    # aplicacion. Es deliberadamente alto: no busca moderar el uso normal, solo
    # cortar una inundacion. Los limites finos van por endpoint en
    # app/utils/limitador.py. Los archivos estaticos quedan fuera de la cuenta.
    RATELIMIT_DEFAULT = os.environ.get(
        'LIMITE_GENERAL', '120 per minute;2000 per hour')

    # Ventana deslizante en vez de ventana fija: con ventana fija se puede
    # gastar el cupo entero al final de un minuto y otro tanto al empezar el
    # siguiente, o sea el doble del limite en dos segundos.
    RATELIMIT_STRATEGY = 'moving-window'

    # Cabeceras X-RateLimit-* en la respuesta, para poder diagnosticar por que
    # alguien recibe un 429 sin tener que leer los logs del servidor.
    RATELIMIT_HEADERS_ENABLED = True

    # --- Desafio anti-bot (autoalojado, sin servicios externos) ---

    # Protege registro publico y recuperacion de contrasena. Se puede apagar:
    # dejar a la gente sin poder registrarse es peor que el spam que evita.
    CAPTCHA_ACTIVO = os.environ.get('CAPTCHA_ACTIVO', 'true').lower() != 'false'

    # Tamano del espacio de busqueda de la prueba de trabajo. Mas alto = mas
    # caro para un bot, pero tambien mas espera en un celular viejo. 60000
    # ronda la decima de segundo en un telefono de gama baja.
    CAPTCHA_DIFICULTAD = int(os.environ.get('CAPTCHA_DIFICULTAD', '60000'))

    # --- Generalidades institucionales del carnet ---
    # Regional, centro, aseguradora, telefono y poliza NO pueden estar escritos
    # dentro de las plantillas: si el sistema se instala en otro centro del
    # SENA, cambiarlos tendria que ser editar el .env, no buscar y reemplazar
    # cadenas por todo el repositorio. Los valores por defecto son los del
    # centro donde nacio el proyecto, para que una instalacion existente no
    # cambie de comportamiento al actualizar.
    GENERALIDADES = {
        'entidad': os.environ.get('CARNET_ENTIDAD', 'SENA'),
        'entidad_larga': os.environ.get(
            'CARNET_ENTIDAD_LARGA', 'Servicio Nacional de Aprendizaje'),
        'regional': os.environ.get('CARNET_REGIONAL', 'Regional Santander'),
        'centro': os.environ.get(
            'CARNET_CENTRO', 'Centro de Gestión Agroempresarial del Oriente'),
        'municipio': os.environ.get('CARNET_MUNICIPIO', 'Vélez'),
        # Bloque de la poliza estudiantil: solo se imprime en el carnet de
        # aprendiz. Si la aseguradora se deja vacia, el bloque no se pinta.
        'aseguradora': os.environ.get('CARNET_ASEGURADORA', 'Aseguradora Aurora'),
        'aseguradora_tel': os.environ.get(
            'CARNET_ASEGURADORA_TEL', '601-7443718 Op. 1'),
        'poliza': os.environ.get('CARNET_POLIZA', '100603'),
    }
