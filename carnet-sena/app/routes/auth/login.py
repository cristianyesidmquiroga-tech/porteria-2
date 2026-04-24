from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, current_user
from ...models.usuarios import Usuario, Rol
from ... import db
import secrets
from datetime import datetime, timedelta
from . import bp

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        identificador = request.form.get('correo') or request.form.get('identificador')
        contraseña = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = Usuario.query.filter(
            (Usuario.correo == identificador) | (Usuario.documento == identificador)
        ).first()

        if user:
            # Detección de Bloqueo
            if user.bloqueado_hasta and datetime.utcnow() < user.bloqueado_hasta:
                segundos = (user.bloqueado_hasta - datetime.utcnow()).total_seconds()
                msg = 'Perfil bloqueado temporalmente por demasiados intentos.'
                if is_ajax: return {"status": "error", "message": msg, "bloqueado_segundos": int(segundos)}, 403
                return render_template('auth/login.html', error_bloqueo=msg, identificador=identificador, bloqueado_segundos=int(segundos))

            if user.check_password(contraseña):
                user.intentos_fallidos = 0
                user.bloqueado_hasta = None
                
                token = secrets.token_hex(16)
                user.session_token = token
                db.session.commit()

                login_user(user, remember=remember)
                session['session_token'] = token
                # Inicializar el tiempo de actividad para evitar expiración inmediata por cookies viejas
                from datetime import timezone
                session['last_activity'] = datetime.now(timezone.utc).timestamp()

                if not user.correo_verificado:
                    msg = 'Debes verificar tu correo.'
                    if is_ajax: return {"status": "success", "message": msg, "redirect": url_for('auth.verificar_correo')}
                    flash(msg, 'warning')
                    return redirect(url_for('auth.verificar_correo'))

                if not user.perfil_completo:
                    msg = f'Bienvenido {user.nombre}. Por favor, actualiza tu perfil.'
                    if is_ajax: return {"status": "success", "message": msg, "redirect": url_for('usuarios.profile')}
                    flash(msg, 'info')
                    return redirect(url_for('usuarios.profile'))

                # Lógica específica para Celadores (Turnos)
                if user.cargo == 'Celador':
                    from app.models.usuarios import TurnoCelador
                    from datetime import date
                    active_turno = TurnoCelador.query.filter(
                        TurnoCelador.celador_id == user.id,
                        TurnoCelador.estado == 'Activo',
                        db.func.date(TurnoCelador.fecha_ingreso) == date.today()
                    ).first()
                    if not active_turno:
                        db.session.add(TurnoCelador(celador_id=user.id, estado='Activo'))
                        db.session.commit()
                    
                    if is_ajax: return {"status": "success", "redirect": url_for('usuarios.profile')}
                    return redirect(url_for('usuarios.profile'))

                if user.puede_operar_porteria:
                    redirect_url = url_for('porteria.dashboard')
                else:
                    redirect_url = url_for('usuarios.profile')

                if is_ajax: return {"status": "success", "redirect": redirect_url}
                return redirect(redirect_url)
            else:
                user.intentos_fallidos += 1
                if user.intentos_fallidos >= 5:
                    user.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=10)
                    db.session.commit()
                    msg = 'Bloqueado por 10 min. Demasiados intentos.'
                    if is_ajax: return {"status": "error", "message": msg, "bloqueado_segundos": 600}, 403
                    return render_template('auth/login.html', error_bloqueo=msg, identificador=identificador, bloqueado_segundos=600)
                else:
                    db.session.commit()
                    msg = f'Credenciales incorrectas. Intento {user.intentos_fallidos} de 5.'
                    if is_ajax: return {"status": "error", "message": msg}, 401
                    flash(msg, 'danger')
        else:
            msg = 'Usuario no encontrado.'
            if is_ajax: return {"status": "error", "message": msg}, 401
            flash(msg, 'danger')

    return render_template('auth/login.html')

@bp.route('/cambiar_password_obligatorio', methods=['GET', 'POST'])
def cambiar_password_obligatorio():
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    if not getattr(current_user, 'debe_cambiar_contrasena', False):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        nueva_contraseña = request.form.get('nueva_contrasena')
        confirmacion = request.form.get('confirmar_contrasena')

        if not nueva_contraseña or not confirmacion:
            flash('Debes llenar ambos campos.', 'danger')
        elif nueva_contraseña != confirmacion:
            flash('Las contraseñas no coinciden.', 'danger')
        elif len(nueva_contraseña) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
        else:
            current_user.contraseña = generate_password_hash(nueva_contraseña)
            current_user.debe_cambiar_contrasena = False
            db.session.commit()
            flash('¡Contraseña actualizada exitosamente! Ahora completa tu perfil.', 'success')
            return redirect(url_for('usuarios.profile'))

    return render_template('auth/cambio_obligatorio.html')
