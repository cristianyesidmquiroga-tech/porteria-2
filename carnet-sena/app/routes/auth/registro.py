from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from ...models.usuarios import Usuario, Rol
from ... import db
import random
import string
import re
from datetime import datetime, timedelta
from ...utils.security import sanitize_html
from . import bp

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.es_admin:
        flash("Acceso denegado. Solo los administradores pueden crear nuevas cuentas.", "danger")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 1. Datos Básicos
        nombre_raw = request.form.get('nombre')
        nombre = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', nombre_raw).strip().title() if nombre_raw else None
        
        correo = sanitize_html(request.form.get('correo')).lower().strip()
        documento_raw = sanitize_html(request.form.get('documento')).strip()
        documento = documento_raw if documento_raw else None
        contraseña = request.form.get('password')

        # 2. Selección de Cargo (Diferenciador principal ahora)
        cargo = request.form.get('cargo')
        if not cargo:
            msg = "Debes seleccionar un cargo o tipo de usuario."
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 3. Asignación Automática de Rol 'Usuario'
        rol_usuario = Rol.query.filter_by(nombre='Usuario').first()
        if not rol_usuario:
            msg = "Error de Sistema: Rol base no encontrado."
            if is_ajax: return {"status": "error", "message": msg}, 500
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 4. Datos Dinámicos por Cargo
        ficha = sanitize_html(request.form.get('ficha')).strip() if cargo == 'Aprendiz' else None
        horario = request.form.get('horario') if cargo == 'Aprendiz' else None
        programa_raw = request.form.get('programa')
        programa = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s0-9]', '', programa_raw).strip() if programa_raw else None

        # 5. Validaciones de Existencia
        if Usuario.query.filter_by(correo=correo).first():
            msg = f'El correo {correo} ya está registrado.'
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))
            
        if documento and Usuario.query.filter_by(documento=documento).first():
            msg = f'El documento {documento} ya se encuentra registrado.'
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 6. Lógica de Consistencia (Solo para Aprendices)
        if cargo == 'Aprendiz' and ficha:
            # Ahora buscamos consistencia por cargo, no por rol_id
            existing = Usuario.query.filter(Usuario.ficha == ficha, Usuario.cargo == 'Aprendiz').first()
            if existing and (existing.programa.lower() != (programa or "").lower() or existing.horario != horario):
                msg = "Consistencia de ficha fallida. Verifica Programa/Jornada para esta ficha."
                if is_ajax: return {"status": "error", "message": msg}, 400
                flash(msg, 'danger')
                return redirect(url_for('auth.register'))

        try:
            new_user = Usuario(
                nombre=nombre,
                documento=documento,
                correo=correo,
                rol_id=rol_usuario.id, # Siempre Rol Usuario
                ficha=ficha,
                programa=programa,
                horario=horario,
                cargo=cargo,
                correo_verificado=False)
            
            new_user.set_password(contraseña)
            new_user.codigo_verificacion = ''.join(random.choices(string.digits, k=6))
            new_user.codigo_expiracion = datetime.utcnow() + timedelta(minutes=15)

            db.session.add(new_user)
            db.session.commit()

            # Logging
            print(f"\n[REGISTRO] {correo} registrado como {cargo}")
            
            try:
                with open('CODIGOS_DESARROLLO.txt', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Registro: {correo} ({cargo}) -> CODIGO: {new_user.codigo_verificacion}\n")
            except: pass

            msg = '¡Registro exitoso! Revisa tu correo.'
            if is_ajax: return {"status": "success", "message": msg, "redirect": url_for('auth.login')}
            flash(msg, 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR REGISTRO] {str(e)}")
            if is_ajax: return {"status": "error", "message": "Error interno al procesar el registro."}, 500
            flash("Error interno durante el registro.", 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')
