from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from . import porteria_bp as bp
from ...models.usuarios import Usuario, Rol
from ...models.accesos import Acceso
from ... import db

@bp.route('/analytics/<rol_nombre>')
@login_required
def analytics(rol_nombre):
    if not current_user.puede_operar_porteria:
        flash('No tienes permiso para ver reportes de usuarios.', 'danger')
        return redirect(url_for('porteria.dashboard'))

    colombia_tz = timezone(timedelta(hours=-5))
    start_utc_7d = datetime.utcnow() - timedelta(days=8)
    today_local = datetime.now(colombia_tz).date()

    # Consulta ajustada a Cargo en lugar de Rol
    entries = db.session.query(Acceso.fecha, Usuario).join(Usuario, Acceso.referencia_id == Usuario.id).filter(
        Acceso.fecha >= start_utc_7d, 
        Acceso.tipo == 'Entrada', 
        Acceso.tipo_referencia == 'Usuario', 
        Usuario.cargo == rol_nombre
    ).all()

    counts_hoy, counts_7dias, subcharts_hoy, subcharts_7dias = {}, {}, {}, {}

    for fecha_utc, u in entries:
        if isinstance(fecha_utc, str):
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                try: fecha_utc = datetime.strptime(fecha_utc, fmt); break
                except ValueError: continue

        fecha_local = fecha_utc.replace(tzinfo=timezone.utc).astimezone(colombia_tz)
        d_local = fecha_local.date()
        
        if rol_nombre == 'Aprendiz':
            prog_name = u.programa if u.programa else "Sin Programa Específico"
            cat = f"{prog_name} (Ficha: {u.ficha or 'S/F'})"
            sub_label = f"Ficha {u.ficha or 'S/F'}"
        elif rol_nombre == 'Personal':
            prog_name = "Personal por Cargos / Dependencias"
            cat = u.cargo if u.cargo else "Cargo No Registrado"
            sub_label = cat # Agrupamos por cargo directamente en las tajadas
        else: # Instructor u otros
            prog_name = u.programa if u.programa else "Área / Especialidad"
            cat = prog_name
            sub_label = u.nombre

        counts_7dias[cat] = counts_7dias.get(cat, 0) + 1
        if prog_name not in subcharts_7dias: subcharts_7dias[prog_name] = {}
        if prog_name not in subcharts_hoy: subcharts_hoy[prog_name] = {}
        subcharts_7dias[prog_name][sub_label] = subcharts_7dias[prog_name].get(sub_label, 0) + 1

        if d_local == today_local:
            counts_hoy[cat] = counts_hoy.get(cat, 0) + 1
            subcharts_hoy[prog_name][sub_label] = subcharts_hoy[prog_name].get(sub_label, 0) + 1

    counts_hoy = dict(sorted(counts_hoy.items(), key=lambda x: x[1], reverse=True))
    counts_7dias = dict(sorted(counts_7dias.items(), key=lambda x: x[1], reverse=True))

    program_charts = sorted([{
        'prog_name': p, 'hoy_labels': list(subcharts_hoy.get(p, {}).keys()), 'hoy_data': list(subcharts_hoy.get(p, {}).values()),
        'seven_labels': list(subcharts_7dias.get(p, {}).keys()), 'seven_data': list(subcharts_7dias.get(p, {}).values()),
    } for p in set(list(subcharts_hoy.keys()) + list(subcharts_7dias.keys()))], key=lambda x: sum(x['seven_data']), reverse=True)

    analisis = f"Hoy ha ingresado una mayoría de personas pertenecientes a '{list(counts_hoy.keys())[0]}' con {list(counts_hoy.values())[0]} registros." if counts_hoy else f"Aún no hay ingresos de {rol_nombre}s registrados el día de hoy."

    todos_usuarios_rol = Usuario.query.filter_by(cargo=rol_nombre).all()
    usuarios_adentro = []
    for u in todos_usuarios_rol:
        ultimo_acceso = Acceso.query.filter_by(referencia_id=u.id, tipo_referencia='Usuario').order_by(Acceso.fecha.desc()).first()
        if ultimo_acceso and ultimo_acceso.tipo == 'Entrada':
            usuarios_adentro.append({
                "nombre": u.nombre,
                "documento": u.documento,
                "programa": u.programa or u.cargo or "N/A",
                "ficha": u.ficha or "N/A",
                "hora_ingreso": ultimo_acceso.fecha.replace(tzinfo=timezone.utc).astimezone(colombia_tz).strftime('%I:%M %p')
            })

    return render_template('porteria/analytics_rol.html', rol_nombre=rol_nombre, chart_data={'hoy_labels': list(counts_hoy.keys()), 'hoy_data': list(counts_hoy.values()), '7d_labels': list(counts_7dias.keys()), '7d_data': list(counts_7dias.values())}, program_charts=program_charts, analisis=analisis, usuarios_adentro=usuarios_adentro)

@bp.route('/historial_clases', methods=['GET', 'POST'])
@login_required
def historial_clases():
    if not current_user.es_admin:
        flash('No tienes permiso para ver el historial de clases.', 'danger')
        return redirect(url_for('usuarios.profile'))
    from ...models.asistencia import AsistenciaClase
    busqueda_ficha = request.form.get('ficha') if request.method == 'POST' else None
    historial = []
    if busqueda_ficha:
        historial = db.session.query(AsistenciaClase).filter(
            AsistenciaClase.ficha == busqueda_ficha.strip()
        ).order_by(AsistenciaClase.fecha.desc()).limit(100).all()
    return render_template('porteria/historial_clases.html', historial=historial, busqueda_ficha=busqueda_ficha)
