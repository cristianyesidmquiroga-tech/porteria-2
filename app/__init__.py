from flask import Flask, session, redirect, url_for, flash, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, logout_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_apscheduler import APScheduler
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta, timezone
import logging
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()

# El limitador se define en su propio modulo junto al catalogo de limites.
from .utils.limitador import (  # noqa: E402
    aplicar_limites, limiter, registrar_manejador_429)

# Inactividad permitida para usuarios que no operan porteria.
TIEMPO_INACTIVIDAD_SEGUNDOS = 10 * 60


def _registrar_cabeceras_seguridad(app):
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), payment=(), usb=(), camera=(self)'
        )
        # Aisla la pestana de cualquier ventana que la haya abierto: sin esto,
        # una pagina externa que abra el sistema conserva una referencia viva a
        # la ventana (window.opener) y puede redirigirla a una copia falsa del
        # login. No rompe nada aqui porque el sistema no usa ventanas emergentes.
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        # Impide que un Flash/PDF antiguo alojado en otro dominio se traiga
        # datos de este. Cuesta una cabecera y cierra un vector heredado.
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        # HSTS solo cuando la peticion llego por HTTPS, para no romper el
        # desarrollo local en HTTP.
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )

        # CSP. script-src ya no lleva 'unsafe-inline': los manejadores inline
        # se migraron a addEventListener en archivos de /static/js, y los
        # datos que antes se incrustaban en el HTML viajan en atributos
        # data-*. Sin 'unsafe-inline' un XSS almacenado no llega a ejecutarse,
        # que es la defensa que importa aqui (el sistema guarda cedulas,
        # fotos de rostro y tipo de sangre).
        # style-src si lo conserva: los estilos inline son muchisimos mas y
        # no abren la puerta a ejecucion de codigo.
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net "
            # unpkg.com se quito: la unica libreria que venia de ahi era el
            # lector html5-qrcode, que ahora se sirve desde /static con la
            # version fijada en el nombre del archivo.
            "https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
            "https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            # ui-avatars.com se elimino: recibia el nombre real de cada
            # usuario en la URL, es decir datos personales enviados a un
            # tercero en cada carga de pagina. Ahora los avatares son SVG
            # locales servidos desde 'self'.
            "img-src 'self' data: blob: https://upload.wikimedia.org; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none'"
        )
        return response


def _registrar_manejadores_error(app):
    @app.errorhandler(413)
    def archivo_muy_grande(error):
        flash("El archivo es demasiado pesado (maximo 10MB).", "danger")
        return redirect(url_for('usuarios.profile'))

    @app.errorhandler(CSRFError)
    def csrf_invalido(error):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"status": "error",
                    "message": "Tu sesion expiro. Recarga la pagina."}, 400
        flash("Tu sesion expiro. Vuelve a intentarlo.", "warning")
        return redirect(url_for('auth.login'))

    @app.errorhandler(404)
    def no_encontrado(error):
        return render_template('errores/404.html'), 404

    @app.errorhandler(500)
    def error_interno(error):
        db.session.rollback()
        app.logger.exception("Error interno no controlado")
        return render_template('errores/500.html'), 500


# Columnas que db.create_all() no puede anadir a tablas que ya existen.
# Cada entrada corre solo si la columna falta, asi que es idempotente.
COLUMNAS_PENDIENTES = {
    'objetos_externos': {
        'serial': 'VARCHAR(100)',
        'propietario': 'VARCHAR(100)',
        'motivo': 'TEXT',
        'activo': 'BOOLEAN DEFAULT TRUE',
        'qr_code': 'VARCHAR(255)',
        'fecha_creacion': 'TIMESTAMP',
    },
    'usuarios': {
        'intentos_codigo': 'INTEGER DEFAULT 0',
        'foto_estado': "VARCHAR(20) DEFAULT 'sin_foto'",
        'foto_motivo': 'TEXT',
        'foto_revisada_por': 'INTEGER',
        'foto_fecha_revision': 'TIMESTAMP',
        'foto_fecha_subida': 'TIMESTAMP',
        'tipo_documento': "VARCHAR(5) DEFAULT 'CC'",
        'tutorial_visto': 'BOOLEAN DEFAULT FALSE',
        # Nombres y apellidos por separado, que es como los pide el carnet
        # oficial. No se rellenan partiendo `nombre`: quedan vacios hasta que
        # la persona los declare (ver el comentario en el modelo).
        'nombres': 'VARCHAR(100)',
        'apellidos': 'VARCHAR(100)',
        # Sin FOREIGN KEY en el ALTER: SQLite no la admite al anadir columna y
        # la integridad ya la impone el modelo al insertar.
        'ficha_id': 'INTEGER',
    },
    'accesos': {
        'operador_id': 'INTEGER',
    },
}


def _migrar_columnas():
    """Anade las columnas que falten en una base creada por una version previa."""
    from sqlalchemy import text, inspect

    registro = logging.getLogger(__name__)
    try:
        inspector = inspect(db.engine)
        tablas = set(inspector.get_table_names())
        for tabla, columnas in COLUMNAS_PENDIENTES.items():
            if tabla not in tablas:
                continue
            existentes = {c['name'] for c in inspector.get_columns(tabla)}
            faltantes = [c for c in columnas if c not in existentes]
            for columna in faltantes:
                db.session.execute(text(
                    f"ALTER TABLE {tabla} ADD COLUMN {columna} {columnas[columna]}"))
            if faltantes:
                registro.info("Migracion %s: columnas agregadas %s", tabla, faltantes)
        db.session.commit()
    except Exception:
        db.session.rollback()
        registro.exception("Fallo la migracion de columnas")


def _registrar_tareas(app):
    from .utils.tareas import auto_exit_all
    from .utils.respaldos import ejecutar_respaldo_mensual

    # Con varios workers de gunicorn cada proceso intentaria programar las
    # mismas tareas. Se puede desactivar por worker con EJECUTAR_TAREAS=false.
    if os.environ.get('EJECUTAR_TAREAS', 'true').lower() == 'false':
        return

    if scheduler.get_jobs():
        return

    scheduler.add_job(
        id='auto_exit_midnight', func=auto_exit_all,
        trigger='cron', hour=0, minute=0, second=5,
        replace_existing=True, misfire_grace_time=3600,
    )
    scheduler.add_job(
        id='respaldo_mensual_db', func=ejecutar_respaldo_mensual,
        trigger='cron', day=1, hour=0, minute=0, second=10,
        replace_existing=True, misfire_grace_time=3600,
    )
    scheduler.start()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.config.Config')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    # Detras de Coolify/Traefik la IP que ve Flask es la del proxy, no la del
    # cliente: sin esto TODO el trafico compartiria un solo contador de limite
    # y el primero en pasarse bloquearia al centro entero. PROXIES_CONFIABLES
    # debe valer exactamente el numero de proxies propios que hay delante; con
    # un valor mas alto que el real, cualquiera podria falsear su IP mandando
    # una cabecera X-Forwarded-For a mano.
    proxies = app.config['PROXIES_CONFIABLES']
    if proxies:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies,
                                x_host=proxies)

    db.init_app(app)
    login_manager.init_app(app)
    # El limitador se inicializa ANTES que CSRF a proposito: los before_request
    # corren en orden de registro, y si CSRF fuera primero, una avalancha de
    # POST con token invalido se respondería con 400 sin gastar nunca el techo
    # general, es decir sin llegar a frenarse. (Los limites por endpoint si se
    # evaluan despues de CSRF, dentro de la vista.)
    limiter.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, inicia sesion para acceder a esta pagina."
    login_manager.login_message_category = "info"

    from .utils.security import check_security_and_verification
    app.before_request(check_security_and_verification)

    @app.before_request
    def check_session_timeout():
        if not current_user.is_authenticated:
            return None

        if getattr(current_user, 'debe_cambiar_contrasena', False):
            permitidos = ['auth.cambiar_password_obligatorio', 'auth.logout',
                          'static', 'main.politica_privacidad', 'main.salud']
            if request.endpoint not in permitidos:
                flash("Por seguridad, debes cambiar tu contrasena temporal antes de continuar.",
                      "warning")
                return redirect(url_for('auth.cambiar_password_obligatorio'))

        ahora = datetime.now(timezone.utc).timestamp()
        ultima = session.get('last_activity')

        # El personal de porteria tiene una ventana mas larga porque opera el
        # escaner durante todo el turno, pero ya no es una sesion sin caducidad.
        if current_user.puede_operar_porteria:
            limite = app.config['PERMANENT_SESSION_LIFETIME'].total_seconds()
            session.permanent = True
        else:
            limite = TIEMPO_INACTIVIDAD_SEGUNDOS

        if ultima and (ahora - ultima) > limite:
            logout_user()
            session.clear()
            flash("Tu sesion expiro por inactividad.", "warning")
            return redirect(url_for('auth.login'))

        session['last_activity'] = ahora
        return None

    with app.app_context():
        from .models import (usuarios, accesos, movimientos, entidades,  # noqa: F401
                             asistencia, mensajes, fichas)

        from .routes.main import bp as main_bp
        from .routes.auth import bp as auth_bp
        from .routes.usuarios import bp as usuarios_bp
        from .routes.equipos import bp as equipos_bp
        from .routes.porteria import porteria_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(usuarios_bp)
        app.register_blueprint(porteria_bp)
        app.register_blueprint(equipos_bp)

        # Debe ir despues de registrar los blueprints: el catalogo trabaja
        # sobre las vistas ya registradas.
        aplicar_limites(app)

        db.create_all()
        _migrar_columnas()
        _registrar_tareas(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models.usuarios import Usuario
        return db.session.get(Usuario, int(user_id))

    _registrar_cabeceras_seguridad(app)
    _registrar_manejadores_error(app)
    registrar_manejador_429(app)

    @app.context_processor
    def _inyectar_captcha():
        """Las plantillas solo pintan el desafio si esta activo."""
        return {'captcha_activo': app.config['CAPTCHA_ACTIVO']}

    @app.template_filter('codigo_barras')
    def _filtro_codigo_barras(dato):
        """Convierte un texto en el SVG de su codigo de barras Code128.

        Se expone como filtro para que las plantillas que muestran pases
        (visitantes, vehiculos, objetos) no tengan que pasar por la vista.
        """
        from markupsafe import Markup
        from .utils.barras import codigo128_svg, DatoNoCodificable
        if not dato:
            return ''
        try:
            return Markup(codigo128_svg(str(dato), alto=90, mostrar_texto=True))
        except DatoNoCodificable:
            return ''

    @app.context_processor
    def inyectar_generalidades():
        """Regional, centro y poliza disponibles en TODAS las plantillas.

        Se inyectan aqui para que ninguna vista vuelva a escribirlos a mano:
        cambiar de centro debe ser cambiar el .env, no editar plantillas.
        """
        return {'generalidades': app.config['GENERALIDADES']}

    @app.context_processor
    def inject_backup_warning():
        if not (current_user.is_authenticated and current_user.es_admin):
            return {'backup_warning': None}

        colombia_tz = timezone(timedelta(hours=-5))
        ahora = datetime.now(colombia_tz)
        if ahora.month == 12:
            proximo_mes = ahora.replace(year=ahora.year + 1, month=1, day=1,
                                        hour=0, minute=0, second=0, microsecond=0)
        else:
            proximo_mes = ahora.replace(month=ahora.month + 1, day=1,
                                        hour=0, minute=0, second=0, microsecond=0)

        dias_restantes = (proximo_mes - ahora).days
        aviso = None
        if dias_restantes <= 3 and not session.get('backup_warn_3'):
            aviso = (f"ATENCION: faltan {dias_restantes} dias para la limpieza "
                     "automatica de la base de datos.")
            session['backup_warn_3'] = True
        elif dias_restantes == 15 and not session.get('backup_warn_15'):
            aviso = ("Aviso (15 dias): el sistema hara un respaldo y limpieza de "
                     "datos antiguos el primer dia del mes.")
            session['backup_warn_15'] = True

        return {'backup_warning': aviso}

    return app
