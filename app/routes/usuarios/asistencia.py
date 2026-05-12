from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...models.usuarios import Usuario
from ...models.accesos import Acceso
from ... import db
from datetime import datetime
from . import bp

@bp.route('/asistencia', methods=['GET', 'POST'])
@login_required
def asistencia():
    if not current_user.puede_gestionar_asistencia:
        flash('Acceso restringido. Solo Instructores o Administradores pueden gestionar asistencia.', 'danger')
        return redirect(url_for('usuarios.profile'))

    students = []
    ficha_raw = request.form.get('ficha') if request.method == 'POST' else None
    ficha = str(ficha_raw).strip() if ficha_raw else None

    if request.method == 'POST':
        action = request.form.get('action', 'buscar')
        
        if action == 'buscar':
            today = datetime.now().date()
            # Grouping to avoid duplicates if they entered multiple times
            students = Usuario.query.join(Acceso, Acceso.referencia_id == Usuario.id).filter(
                Usuario.ficha == ficha,
                db.func.date(Acceso.fecha) == today,
                Acceso.tipo == 'Entrada',
                Acceso.tipo_referencia == 'Usuario'
            ).all()
            # En SQLite/SQLAlchemy básico, es más fácil filtrar en Python los distintos
            students = list({s.id: s for s in students}.values())

        elif action == 'guardar_asistencia':
            ficha_id = request.form.get('ficha_guardar')
            estudiantes_presentes = request.form.getlist('presente')
            
            try:
                today = datetime.now().date()
                students_to_mark = Usuario.query.join(Acceso, Acceso.referencia_id == Usuario.id).filter(
                    Usuario.ficha == ficha_id,
                    db.func.date(Acceso.fecha) == today,
                    Acceso.tipo == 'Entrada',
                    Acceso.tipo_referencia == 'Usuario'
                ).all()
                students_to_mark = list({s.id: s for s in students_to_mark}.values())

                from ...models.asistencia import AsistenciaClase
                for s in students_to_mark:
                    is_present = str(s.id) in estudiantes_presentes
                    nueva_clase = AsistenciaClase(
                        instructor_id=current_user.id,
                        aprendiz_id=s.id,
                        ficha=ficha_id,
                        presente=is_present
                    )
                    db.session.add(nueva_clase)
                
                db.session.commit()
                msg = 'Reporte guardado exitosamente.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return {"status": "success", "message": msg, "redirect": url_for('usuarios.asistencia')}
                flash(msg, 'success')
                return redirect(url_for('usuarios.asistencia'))
            except Exception as e:
                db.session.rollback()
                msg = f'Error al guardar asistencia: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return {"status": "error", "message": msg}, 400
                flash(msg, 'danger')
                return redirect(url_for('usuarios.asistencia'))

    return render_template('usuarios/asistencia.html',
                           students=students, ficha=ficha)
