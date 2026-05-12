from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ... import db
import random
import string
from datetime import datetime, timedelta
from . import bp

@bp.route('/verificar', methods=['GET', 'POST'])
@login_required
def verificar_correo():
    if getattr(current_user, 'correo_verificado', False):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        if getattr(current_user, 'codigo_verificacion', '') == codigo:
            if current_user.codigo_expiracion and datetime.utcnow() > current_user.codigo_expiracion:
                flash('El código ha expirado. Por favor, solicita uno nuevo.', 'danger')
                return redirect(url_for('auth.verificar_correo'))

            current_user.correo_verificado = True
            current_user.codigo_verificacion = None
            current_user.codigo_expiracion = None
            db.session.commit()

            flash('¡Correo verificado exitosamente!', 'success')
            if not getattr(current_user, 'perfil_completo', True):
                return redirect(url_for('usuarios.profile'))
            return redirect(url_for('main.index'))
        else:
            flash('Código incorrecto. Intenta nuevamente.', 'danger')

    if current_user.codigo_verificacion:
        print(f"\n[ACCESO] Codigo para {current_user.correo}: {current_user.codigo_verificacion}", flush=True)
        # Registro en Archivo (Fail-safe)
        try:
            with open('CODIGOS_DESARROLLO.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Acceso: {current_user.correo} -> CODIGO: {current_user.codigo_verificacion}\n")
        except: pass

    return render_template('auth/verificar.html')

@bp.route('/reenviar_codigo', methods=['POST'])
@login_required
def reenviar_codigo():
    if not getattr(current_user, 'correo_verificado', False):
        current_user.codigo_verificacion = ''.join(random.choices(string.digits, k=6))
        current_user.codigo_expiracion = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        
        print("\n" + "=" * 50, flush=True)
        print(f"REENVIO DE CORREO A: {current_user.correo}", flush=True)
        print(f"NUEVO CODIGO DE VERIFICACION: {current_user.codigo_verificacion}", flush=True)
        print("=" * 50 + "\n", flush=True)

        # Registro en Archivo (Fail-safe)
        try:
            with open('CODIGOS_DESARROLLO.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Reenvio: {current_user.correo} -> CODIGO: {current_user.codigo_verificacion}\n")
        except: pass

        flash('Se ha reenviado un nuevo código a tu correo.', 'info')
    return redirect(url_for('auth.verificar_correo'))
