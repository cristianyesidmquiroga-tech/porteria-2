from flask import render_template, redirect, url_for, flash, request, session
from ... import db
from ...models.usuarios import Usuario
from . import bp
import random
import string
from datetime import datetime, timedelta, timezone

@bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar_solicitar():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        usuario = Usuario.query.filter_by(correo=email).first()
        
        if usuario:
            # Generar código de 6 dígitos
            codigo = ''.join(random.choices(string.digits, k=6))
            usuario.codigo_recuperacion = codigo
            usuario.recuperacion_expiracion = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            
            # Simulación de Envío (Copia del patrón de verificación)
            print("\n" + "=" * 50, flush=True)
            print(f"RECUPERACIÓN DE CONTRASEÑA PARA: {usuario.correo}", flush=True)
            print(f"CÓDIGO DE RECUPERACIÓN: {codigo}", flush=True)
            print("=" * 50 + "\n", flush=True)

            try:
                with open('CODIGOS_DESARROLLO.txt', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Recuperación: {usuario.correo} -> CÓDIGO: {codigo}\n")
            except: pass
            
            session['recovery_email'] = email
            flash('Se ha enviado un código de recuperación a tu correo.', 'info')
            return redirect(url_for('auth.recuperar_verificar'))
        else:
            flash('No encontramos ninguna cuenta asociada a ese correo.', 'danger')
            
    return render_template('auth/recuperar_paso1.html')

@bp.route('/recuperar/verificar', methods=['GET', 'POST'])
def recuperar_verificar():
    email = session.get('recovery_email')
    if not email:
        return redirect(url_for('auth.recuperar_solicitar'))
    
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        usuario = Usuario.query.filter_by(correo=email).first()
        
        if usuario and usuario.codigo_recuperacion == codigo:
            # Verificar expiración
            now = datetime.now(timezone.utc)
            # Asegurar que el objeto de db tenga timezone si se guardó como UTC o manejarlo localmente
            expiracion = usuario.recuperacion_expiracion
            if expiracion and expiracion.replace(tzinfo=timezone.utc) < now:
                flash('El código ha expirado. Por favor, solicita uno nuevo.', 'warning')
                return redirect(url_for('auth.recuperar_solicitar'))
            
            session['recovery_verified'] = True
            flash('Código verificado con éxito. Ahora puedes cambiar tu contraseña.', 'success')
            return redirect(url_for('auth.recuperar_cambiar'))
        else:
            flash('El código ingresado es incorrecto.', 'danger')
            
    return render_template('auth/recuperar_paso2.html', email=email)

@bp.route('/recuperar/cambiar', methods=['GET', 'POST'])
def recuperar_cambiar():
    email = session.get('recovery_email')
    verified = session.get('recovery_verified')
    
    if not email or not verified:
        flash('Debes verificar tu código antes de cambiar la contraseña.', 'warning')
        return redirect(url_for('auth.recuperar_solicitar'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 4:
            flash('La contraseña debe tener al menos 4 caracteres.', 'warning')
        elif password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
        else:
            usuario = Usuario.query.filter_by(correo=email).first()
            if usuario:
                usuario.set_password(password)
                usuario.codigo_recuperacion = None
                usuario.recuperacion_expiracion = None
                db.session.commit()
                
                # Limpiar sesión de recuperación
                session.pop('recovery_email', None)
                session.pop('recovery_verified', None)
                
                flash('Tu contraseña ha sido actualizada correctamente. Ya puedes iniciar sesión.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Ocurrió un error inesperado.', 'danger')
                return redirect(url_for('auth.recuperar_solicitar'))
                
    return render_template('auth/recuperar_paso3.html', email=email)
