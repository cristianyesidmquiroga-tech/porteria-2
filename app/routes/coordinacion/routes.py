from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ...models.usuarios import Usuario
from ...models.accesos import Acceso
from ...models.asistencia import AsistenciaClase
from ... import db
from sqlalchemy import func, distinct
from ...utils import get_colombia_time
from . import coordinacion_bp


def _check_acceso():
    if not current_user.puede_ver_ambientes:
        flash('Acceso restringido. Solo Coordinación, Subdirección o Administración.', 'danger')
        return False
    return True


@coordinacion_bp.route('/ambientes')
@login_required
def ambientes():
    if not _check_acceso():
        return redirect(url_for('usuarios.profile'))

    # El reloj del sistema (UTC en el servidor) y el de Colombia no coinciden
    # entre las 0:00 y las 5:00 UTC: con datetime.now() la ficha del dia no
    # aparecia en esas horas. Todo el sistema usa get_colombia_time().
    today = get_colombia_time().date()

    # Fichas con aprendices dentro hoy
    rows = (
        db.session.query(Usuario.ficha, func.count(distinct(Usuario.id)).label('count'))
        .join(Acceso, Acceso.referencia_id == Usuario.id)
        .filter(
            func.date(Acceso.fecha) == today,
            Acceso.tipo == 'Entrada',
            Acceso.tipo_referencia == 'Usuario',
            Usuario.ficha.isnot(None),
            Usuario.ficha != '',
            Usuario.cargo == 'Aprendiz'
        )
        .group_by(Usuario.ficha)
        .order_by(Usuario.ficha)
        .all()
    )

    ambientes_list = []
    for row in rows:
        ficha_num = row.ficha
        count = row.count

        # Programa del primer aprendiz de esa ficha
        muestra = Usuario.query.filter_by(ficha=ficha_num, cargo='Aprendiz').first()
        programa = muestra.programa if muestra and muestra.programa else 'Sin programa'

        # Instructor que tomó asistencia hoy (si existe)
        asistencia_hoy = (
            AsistenciaClase.query
            .filter(
                AsistenciaClase.ficha == ficha_num,
                func.date(AsistenciaClase.fecha) == today
            )
            .first()
        )
        instructor_nombre = 'Sin instructor registrado'
        if asistencia_hoy:
            instr = db.session.get(Usuario, asistencia_hoy.instructor_id)
            if instr:
                instructor_nombre = instr.nombre

        ambientes_list.append({
            'ficha': ficha_num,
            'programa': programa,
            'count': count,
            'instructor': instructor_nombre,
            'asistencia_tomada': asistencia_hoy is not None,
        })

    return render_template(
        'coordinacion/ambientes.html',
        ambientes=ambientes_list,
        today=today
    )


@coordinacion_bp.route('/ambientes/<ficha>')
@login_required
def detalle_ambiente(ficha):
    if not _check_acceso():
        return redirect(url_for('usuarios.profile'))

    today = get_colombia_time().date()

    # Aprendices de esa ficha que entraron hoy
    students_raw = (
        Usuario.query
        .join(Acceso, Acceso.referencia_id == Usuario.id)
        .filter(
            Usuario.ficha == ficha,
            func.date(Acceso.fecha) == today,
            Acceso.tipo == 'Entrada',
            Acceso.tipo_referencia == 'Usuario',
            Usuario.cargo == 'Aprendiz'
        )
        .all()
    )
    students = list({s.id: s for s in students_raw}.values())

    # Hora de llegada de cada aprendiz
    arrival_times = {}
    for s in students:
        entry = (
            Acceso.query
            .filter(
                Acceso.referencia_id == s.id,
                Acceso.tipo_referencia == 'Usuario',
                Acceso.tipo == 'Entrada',
                func.date(Acceso.fecha) == today
            )
            .order_by(Acceso.fecha.asc())
            .first()
        )
        arrival_times[s.id] = entry.fecha if entry else None

    # Instructor de la ficha hoy (de AsistenciaClase)
    asistencias_hoy = (
        AsistenciaClase.query
        .filter(
            AsistenciaClase.ficha == ficha,
            func.date(AsistenciaClase.fecha) == today
        )
        .all()
    )
    instructor = None
    if asistencias_hoy:
        instr_obj = db.session.get(Usuario, asistencias_hoy[0].instructor_id)
        instructor = instr_obj

    # Mapa aprendiz_id -> asistencia para mostrar estado y comentario
    asistencias_map = {a.aprendiz_id: a for a in asistencias_hoy}

    # Programa del ambiente
    muestra = Usuario.query.filter_by(ficha=ficha, cargo='Aprendiz').first()
    programa = muestra.programa if muestra and muestra.programa else 'Sin programa'

    return render_template(
        'coordinacion/detalle_ambiente.html',
        ficha=ficha,
        programa=programa,
        students=students,
        arrival_times=arrival_times,
        instructor=instructor,
        asistencias_map=asistencias_map,
        today=today
    )
