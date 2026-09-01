from flask import render_template, redirect, url_for, flash, request, session
from ... import db
from ...models.usuarios import Usuario
from ...utils import get_colombia_time
from ...utils.security import comparar_codigo, validar_contrasena
from ...utils.captcha import validar_formulario
from . import bp
from datetime import timedelta
import logging
import secrets
import string

logger = logging.getLogger(__name__)

MINUTOS_VIGENCIA_CODIGO = 15
MAX_INTENTOS_CODIGO = 5

# Respuesta unica pase lo que pase: si variara segun si el correo existe,
# cualquiera podria averiguar que cuentas estan registradas.
MENSAJE_NEUTRO = ('Si el correo esta registrado, enviamos un codigo de '
                  'recuperacion. Revisa tu bandeja de entrada.')


@bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar_solicitar():
    if request.method != 'POST':
        return render_template('auth/recuperar_paso1.html')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Desafio anti-bot: este endpoint dispara un correo saliente por peticion,
    # asi que es el otro candidato natural (junto al registro) a ser usado como
    # maquina de spam contra buzones ajenos.
    captcha_ok, error_captcha = validar_formulario()
    if not captcha_ok:
        if is_ajax:
            return {"status": "error", "message": error_captcha}, 400
        flash(error_captcha, 'danger')
        return redirect(url_for('auth.recuperar_solicitar'))

    email = request.form.get('email', '').strip().lower()
    usuario = Usuario.query.filter_by(correo=email).first()

    if usuario:
        codigo = ''.join(secrets.choice(string.digits) for _ in range(6))
        usuario.codigo_recuperacion = codigo
        usuario.recuperacion_expiracion = (
            get_colombia_time() + timedelta(minutes=MINUTOS_VIGENCIA_CODIGO))
        usuario.intentos_codigo = 0
        db.session.commit()

        from ...utils.email import enviar_correo
        cuerpo = render_template('auth/email_recuperacion.html',
                                 usuario=usuario, codigo=codigo)
        enviar_correo(usuario.correo, "Recuperacion de contrasena - SENA", cuerpo)
        logger.info("Codigo de recuperacion emitido para el usuario %s", usuario.id)

    # El correo se guarda en sesion aunque no exista la cuenta, para que el
    # flujo se vea identico en ambos casos.
    session['recovery_email'] = email
    session.pop('recovery_verified', None)

    if is_ajax:
        return {"status": "success", "message": MENSAJE_NEUTRO,
                "redirect": url_for('auth.recuperar_verificar')}
    flash(MENSAJE_NEUTRO, 'info')
    return redirect(url_for('auth.recuperar_verificar'))


@bp.route('/recuperar/verificar', methods=['GET', 'POST'])
def recuperar_verificar():
    email = session.get('recovery_email')
    if not email:
        return redirect(url_for('auth.recuperar_solicitar'))

    if request.method != 'POST':
        return render_template('auth/recuperar_paso2.html', email=email)

    codigo = request.form.get('codigo', '').strip()
    usuario = Usuario.query.filter_by(correo=email).first()
    ahora = get_colombia_time()

    if not usuario or not usuario.codigo_recuperacion:
        flash('El codigo ingresado es incorrecto o ya fue usado.', 'danger')
        return render_template('auth/recuperar_paso2.html', email=email)

    if usuario.recuperacion_expiracion and ahora > usuario.recuperacion_expiracion:
        usuario.codigo_recuperacion = None
        usuario.recuperacion_expiracion = None
        db.session.commit()
        flash('El codigo expiro. Solicita uno nuevo.', 'warning')
        return redirect(url_for('auth.recuperar_solicitar'))

    if not comparar_codigo(usuario.codigo_recuperacion, codigo):
        # Sin este contador el codigo de 6 digitos se podia probar
        # indefinidamente hasta acertar.
        usuario.intentos_codigo = (usuario.intentos_codigo or 0) + 1
        if usuario.intentos_codigo >= MAX_INTENTOS_CODIGO:
            # Se anula el codigo, pero NO se toca bloqueado_hasta: ese campo lo
            # usa el login, y escribirlo desde un endpoint publico permitiria
            # dejar fuera del sistema al celador de turno a voluntad.
            usuario.codigo_recuperacion = None
            usuario.recuperacion_expiracion = None
            db.session.commit()
            logger.warning("Codigo de recuperacion invalidado por exceso de "
                           "intentos (usuario %s)", usuario.id)
            flash('Demasiados intentos fallidos. El codigo fue anulado, '
                  'solicita uno nuevo.', 'danger')
            return redirect(url_for('auth.recuperar_solicitar'))
        db.session.commit()
        restantes = MAX_INTENTOS_CODIGO - usuario.intentos_codigo
        flash(f'El codigo ingresado es incorrecto. Te quedan {restantes} intentos.',
              'danger')
        return render_template('auth/recuperar_paso2.html', email=email)

    usuario.intentos_codigo = 0
    db.session.commit()
    session['recovery_verified'] = True
    flash('Codigo verificado. Ahora puedes cambiar tu contrasena.', 'success')
    return redirect(url_for('auth.recuperar_cambiar'))


@bp.route('/recuperar/cambiar', methods=['GET', 'POST'])
def recuperar_cambiar():
    email = session.get('recovery_email')
    if not email or not session.get('recovery_verified'):
        flash('Debes verificar tu codigo antes de cambiar la contrasena.', 'warning')
        return redirect(url_for('auth.recuperar_solicitar'))

    if request.method != 'POST':
        return render_template('auth/recuperar_paso3.html', email=email)

    password = request.form.get('password')
    confirmacion = request.form.get('confirm_password')

    error = validar_contrasena(password, confirmacion)
    if error:
        flash(error, 'danger')
        return render_template('auth/recuperar_paso3.html', email=email)

    usuario = Usuario.query.filter_by(correo=email).first()
    if not usuario:
        session.pop('recovery_email', None)
        session.pop('recovery_verified', None)
        flash('Ocurrio un error inesperado. Intenta de nuevo.', 'danger')
        return redirect(url_for('auth.recuperar_solicitar'))

    usuario.set_password(password)
    usuario.codigo_recuperacion = None
    usuario.recuperacion_expiracion = None
    usuario.intentos_codigo = 0
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.debe_cambiar_contrasena = False
    # Invalida cualquier sesion abierta con la contrasena anterior.
    usuario.session_token = None
    db.session.commit()
    logger.info("Contrasena restablecida para el usuario %s", usuario.id)

    session.pop('recovery_email', None)
    session.pop('recovery_verified', None)

    flash('Tu contrasena fue actualizada. Ya puedes iniciar sesion.', 'success')
    return redirect(url_for('auth.login'))
