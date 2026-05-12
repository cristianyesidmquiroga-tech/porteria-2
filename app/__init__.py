from flask import Flask, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta, timezone
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Limitar tamaño de archivos a 10MB (Suficiente para fotos de alta resolución)
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

    # Asegurar que la carpeta de la instancia (donde se guarda la BD) exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
    login_manager.login_message_category = "info"

    @app.before_request
    def check_session_timeout():
        from flask import request
        
        if current_user.is_authenticated:
            # INTERCEPTOR: Cambio de contraseña obligatorio
            if getattr(current_user, 'debe_cambiar_contrasena', False):
                allowed_endpoints = ['auth.cambiar_password_obligatorio', 'auth.logout', 'static']
                if request.endpoint not in allowed_endpoints:
                    flash("Por seguridad, debes cambiar tu contraseña temporal antes de continuar.", "warning")
                    return redirect(url_for('auth.cambiar_password_obligatorio'))
            
            # Determinamos si es personal de portería (Excepción)
            es_personal_porteria = current_user.puede_operar_porteria
            
            if not es_personal_porteria:
                last_activity = session.get('last_activity')
                now = datetime.now(timezone.utc)
                
                if last_activity:
                    # Tiempo de inactividad: 10 minutos
                    if (now.timestamp() - last_activity) > (10 * 60):
                        logout_user()
                        session.clear()
                        flash("Tu sesión ha expirado por inactividad.", "warning")
                        return redirect(url_for('auth.login'))
                
                session['last_activity'] = now.timestamp()
            else:
                # Para celadores, refrescamos last_activity pero no aplicamos el timeout de 10 min
                session['last_activity'] = datetime.now(timezone.utc).timestamp()
                session.permanent = True  # Asegura que la cookie no sea de sesión (que se borre al cerrar navegador)

    with app.app_context():
        # Importar los modelos de la base de datos
        from .models import usuarios, accesos, movimientos, entidades, asistencia  # noqa: F401

        # Registrar los Blueprints (Módulos de rutas)
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

        # Crear las tablas de la base de datos si no existen
        db.create_all()

        # Configurar tareas automáticas (Programador de tareas)
        from .utils.tareas import auto_exit_all
        from .utils.respaldos import ejecutar_respaldo_mensual
        
        # Evitar que se registren las mismas tareas varias veces al recargar el servidor
        if not scheduler.get_jobs():
            # Programar a las 00:00:05 (5 segundos después de medianoche) cada día
            scheduler.add_job(
                id='auto_exit_midnight',
                func=auto_exit_all,
                trigger='cron',
                hour=0,
                minute=0,
                second=5
            )
            # Programar a las 00:00:10 el día 1 de cada mes
            scheduler.add_job(
                id='respaldo_mensual_db',
                func=ejecutar_respaldo_mensual,
                trigger='cron',
                day=1,
                hour=0,
                minute=0,
                second=10
            )
            scheduler.start()

    @login_manager.user_loader
    def load_user(user_id):
        from .models.usuarios import Usuario
        return Usuario.query.get(int(user_id))

    @app.after_request
    def add_header(response):
        """
        Configuración de seguridad y caché.
        """
        # Prevención de Caché (ya existente)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'

        # Cabeceras de Seguridad Hardening
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
        
        # Opcional: CSP básica para permitir solo scripts locales y de fuentes confiables (ej. Google Fonts, ChartJS)
        # response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://use.fontawesome.com; font-src 'self' https://fonts.gstatic.com https://use.fontawesome.com; img-src 'self' data: https://upload.wikimedia.org https://ui-avatars.com;"

        return response

    @app.context_processor
    def inject_backup_warning():
        from flask import session
        if current_user.is_authenticated and current_user.rol.nombre == 'Admin':
            colombia_tz = timezone(timedelta(hours=-5))
            now = datetime.now(colombia_tz)
            
            # Calcular el primer día del próximo mes
            if now.month == 12:
                next_month = now.replace(year=now.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                next_month = now.replace(month=now.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)
                
            days_left = (next_month - now).days
            
            warning_msg = None
            if days_left == 30 and not session.get('backup_warn_30'):
                warning_msg = "Aviso (1 mes): El sistema realizará un respaldo y limpieza de datos antiguos el 1er día del mes."
                session['backup_warn_30'] = True
            elif days_left == 15 and not session.get('backup_warn_15'):
                warning_msg = "Aviso (15 días): El sistema realizará un respaldo y limpieza de datos antiguos el 1er día del mes."
                session['backup_warn_15'] = True
            elif days_left <= 3 and not session.get('backup_warn_3'):
                warning_msg = f"¡ATENCIÓN! Faltan {days_left} días para la limpieza automática de la base de datos."
                session['backup_warn_3'] = True
                
            return {'backup_warning': warning_msg}
        return {'backup_warning': None}

    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash("El archivo es demasiado pesado (Máximo 10MB). Por favor, intenta con una imagen más pequeña.", "danger")
        return redirect(url_for('usuarios.profile'))

    return app
