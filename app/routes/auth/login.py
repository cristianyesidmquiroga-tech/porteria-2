from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, current_user
from ...models.usuarios import Usuario
from ...utils import get_colombia_time
from ...utils.security import format_identificador, validar_contrasena
from ... import db
from datetime import datetime, timedelta, timezone
import logging
import secrets
from . import bp

logger = logging.getLogger(__name__)

MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 10

# Un mensaje unico para "no existe" y "contrasena incorrecta": si difirieran,
# cualquiera podria averiguar que cedulas y correos estan registrados.
CREDENCIALES_INVALIDAS = 'Correo/documento o contrasena incorrectos.'


def _destino_tras_login(user):
    if user.debe_cambiar_contrasena:
        return url_for('auth.cambiar_password_obligatorio')
    if not user.correo_verificado:
        return url_for('auth.verificar_correo')
    if not user.perfil_completo:
        return url_for('usuarios.profile')
    if user.puede_operar_porteria:
        return url_for('porteria.dashboard')
    return url_for('usuarios.profile')


def _abrir_turno_celador(user):
    from ...models.usuarios import TurnoCelador

    turno_activo = TurnoCelador.query.filter(
        TurnoCelador.celador_id == user.id,
        TurnoCelador.estado == 'Activo',
        db.func.date(TurnoCelador.fecha_ingreso) == get_colombia_time().date(),
    ).first()
    if not turno_activo:
        db.session.add(TurnoCelador(celador_id=user.id, estado='Activo'))
        db.session.commit()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method != 'POST':
        return render_template('auth/login.html')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    identificador = format_identificador(
        request.form.get('correo') or request.form.get('identificador'))
    contrasena = request.form.get('password')
    remember = bool(request.form.get('remember'))

    if not identificador or not contrasena:
        if is_ajax:
            return {"status": "error", "message": CREDENCIALES_INVALIDAS}, 401
        flash(CREDENCIALES_INVALIDAS, 'danger')
        return render_template('auth/login.html')

    user = Usuario.query.filter(
        (Usuario.correo == identificador) | (Usuario.documento == identificador)
    ).first()

    ahora = get_colombia_time()

    if user and user.bloqueado_hasta and ahora < user.bloqueado_hasta:
        segundos = int((user.bloqueado_hasta - ahora).total_seconds())
        msg = 'Perfil bloqueado temporalmente por demasiados intentos.'
        if is_ajax:
            return {"status": "error", "message": msg,
                    "bloqueado_segundos": segundos}, 403
        return render_template('auth/login.html', error_bloqueo=msg,
                               identificador=identificador,
                               bloqueado_segundos=segundos)

    if not user or not user.check_password(contrasena):
        if user:
            user.intentos_fallidos = (user.intentos_fallidos or 0) + 1
            if user.intentos_fallidos >= MAX_INTENTOS:
                user.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
                db.session.commit()
                logger.warning("Cuenta %s bloqueada por intentos fallidos", user.id)
                msg = f'Bloqueado por {MINUTOS_BLOQUEO} minutos. Demasiados intentos.'
                if is_ajax:
                    return {"status": "error", "message": msg,
                            "bloqueado_segundos": MINUTOS_BLOQUEO * 60}, 403
                return render_template('auth/login.html', error_bloqueo=msg,
                                       identificador=identificador,
                                       bloqueado_segundos=MINUTOS_BLOQUEO * 60)
            db.session.commit()
        if is_ajax:
            return {"status": "error", "message": CREDENCIALES_INVALIDAS}, 401
        flash(CREDENCIALES_INVALIDAS, 'danger')
        return render_template('auth/login.html', identificador=identificador)

    # --- Credenciales correctas ---
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    token = secrets.token_hex(32)
    user.session_token = token
    db.session.commit()

    login_user(user, remember=remember)
    # Renovar el identificador de sesion tras autenticar evita la fijacion de
    # sesion (que alguien fije una cookie conocida antes del login).
    session['session_token'] = token
    session['last_activity'] = datetime.now(timezone.utc).timestamp()
    session.modified = True

    if user.cargo == 'Celador':
        _abrir_turno_celador(user)

    destino = _destino_tras_login(user)
    logger.info("Inicio de sesion del usuario %s", user.id)

    if is_ajax:
        return {"status": "success", "redirect": destino}
    return redirect(destino)


@bp.route('/cambiar_password_obligatorio', methods=['GET', 'POST'])
def cambiar_password_obligatorio():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if not getattr(current_user, 'debe_cambiar_contrasena', False):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nueva = request.form.get('nueva_contrasena')
        confirmacion = request.form.get('confirmar_contrasena')

        error = validar_contrasena(nueva, confirmacion)
        if error:
            flash(error, 'danger')
        elif current_user.check_password(nueva):
            flash('La nueva contrasena debe ser distinta de la temporal.', 'danger')
        else:
            current_user.set_password(nueva)
            current_user.debe_cambiar_contrasena = False
            db.session.commit()
            flash('Contrasena actualizada correctamente.', 'success')
            if not current_user.correo_verificado:
                return redirect(url_for('auth.verificar_correo'))
            if not current_user.perfil_completo:
                return redirect(url_for('usuarios.profile'))
            return redirect(url_for('main.index'))

    return render_template('auth/cambio_obligatorio.html')
