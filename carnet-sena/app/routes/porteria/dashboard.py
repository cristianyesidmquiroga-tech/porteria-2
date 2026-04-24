from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
import csv
import io
from . import porteria_bp as bp
from ...models.usuarios import Usuario, Rol
from ...models.accesos import Acceso
from ... import db

@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.puede_operar_porteria:
        flash('No tienes permiso para acceder al dashboard de portería.', 'danger')
        return redirect(url_for('usuarios.profile'))

    # Estadísticas clave (KPIs)
    # Estadísticas de usuarios activos por su cargo
    aprendiz_count = Usuario.query.filter_by(cargo='Aprendiz').count()
    instructor_count = Usuario.query.filter_by(cargo='Instructor').count()
    trabajador_count = Usuario.query.join(Rol).filter(Rol.nombre == 'Trabajador').count()

    # Historial de entradas de los últimos 7 días por Cargo (para la gráfica)
    colombia_tz = timezone(timedelta(hours=-5))
    today_local = datetime.now(colombia_tz).date()
    labels_7days = []
    stats_aprendiz = [0] * 7
    stats_instructor = [0] * 7
    stats_trabajador = [0] * 7

    dias_es = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
    day_map = {}
    for i in range(6, -1, -1):
        d = today_local - timedelta(days=i)
        lbl = f"{dias_es[d.weekday()]} {d.day}"
        labels_7days.append(lbl)
        day_map[d] = 6 - i

    start_utc = datetime.utcnow() - timedelta(days=8)
    entries = db.session.query(Acceso.fecha, Usuario.cargo).join(
        Usuario, Acceso.referencia_id == Usuario.id
    ).filter(
        Acceso.fecha >= start_utc,
        Acceso.tipo == 'Entrada',
        Acceso.tipo_referencia == 'Usuario'
    ).all()

    total_entries = 0
    for fecha_utc, cargo in entries:
        if isinstance(fecha_utc, str):
            try: fecha_utc = datetime.strptime(fecha_utc, '%Y-%m-%d %H:%M:%S')
            except ValueError: fecha_utc = datetime.strptime(fecha_utc, '%Y-%m-%d %H:%M:%S.%f')

        fecha_local = fecha_utc.replace(tzinfo=timezone.utc).astimezone(colombia_tz)
        d = fecha_local.date()
        if d in day_map:
            idx = day_map[d]
            if cargo == 'Aprendiz': stats_aprendiz[idx] += 1
            elif cargo == 'Instructor': stats_instructor[idx] += 1
            else: stats_trabajador[idx] += 1  # Trabajador, Celador, Admin, etc.
            total_entries += 1

    max_day_val, max_day_lbl = max(((stats_aprendiz[i] + stats_instructor[i] + stats_trabajador[i], labels_7days[i]) for i in range(7)), default=(-1, ""))
    analisis_texto = f"En los últimos 7 días se registraron {total_entries} ingresos. El día con mayor actividad fue el {max_day_lbl} con {max_day_val} accesos en total." if total_entries > 0 else "Aún no hay suficientes datos para generar un análisis."

    # Historial de accesos y aplicación de filtros
    cargo_filter = request.args.get('cargo')
    ficha_filter = request.args.get('ficha')
    
    # Obtener los cargos y fichas disponibles para llenar los selectores de los filtros
    cargos = [c[0] for c in db.session.query(Usuario.cargo).filter(Usuario.cargo.isnot(None), Usuario.cargo != '').distinct().all()]
    fichas = [f[0] for f in db.session.query(Usuario.ficha).filter(Usuario.ficha.isnot(None), Usuario.ficha != '').distinct().all()]

    history_query = db.session.query(Acceso, Usuario, Rol).join(Usuario, Acceso.referencia_id == Usuario.id).join(Rol, Usuario.rol_id == Rol.id).filter(Acceso.tipo_referencia == 'Usuario')
    if cargo_filter: history_query = history_query.filter(Usuario.cargo == cargo_filter)
    if ficha_filter: history_query = history_query.filter(Usuario.ficha == ficha_filter)
    historial = history_query.order_by(Acceso.fecha.desc()).limit(100).all()

    return render_template('porteria/dashboard.html', kpis={'aprendices': aprendiz_count, 'instructores': instructor_count, 'trabajadores': trabajador_count}, chart_data={'labels': labels_7days, 'aprendices': stats_aprendiz, 'instructores': stats_instructor, 'trabajadores': stats_trabajador}, analisis_texto=analisis_texto, historial=historial, cargos=cargos, fichas=fichas, current_cargo=cargo_filter, current_ficha=ficha_filter)

@bp.route('/export_dashboard')
@login_required
def export_dashboard():
    if not current_user.puede_operar_porteria:
        flash('No tienes permiso para exportar datos.', 'danger')
        return redirect(url_for('usuarios.profile'))

    cargo_filter, ficha_filter = request.args.get('cargo'), request.args.get('ficha')
    history_query = db.session.query(Acceso, Usuario, Rol).join(Usuario, Acceso.referencia_id == Usuario.id).join(Rol, Usuario.rol_id == Rol.id).filter(Acceso.tipo_referencia == 'Usuario')
    if cargo_filter: history_query = history_query.filter(Usuario.cargo == cargo_filter)
    if ficha_filter: history_query = history_query.filter(Usuario.ficha == ficha_filter)
    historial = history_query.order_by(Acceso.fecha.desc()).all()

    def generate():
        yield '\ufeff'
        data = io.StringIO()
        writer = csv.writer(data, delimiter=';')
        writer.writerow(('Documento', 'Nombre Completo', 'Cargo', 'Programa/Especialidad', 'Ficha', 'Equipo(s)', 'Tipo Acceso', 'Fecha', 'Hora'))
        yield data.getvalue(); data.seek(0); data.truncate(0)
        for acceso, usuario, rol in historial:
            colombia_tz = timezone(timedelta(hours=-5))
            fecha_utc = acceso.fecha
            if isinstance(fecha_utc, str):
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                    try: fecha_utc = datetime.strptime(fecha_utc, fmt); break
                    except ValueError: continue
            if isinstance(fecha_utc, datetime):
                fecha_local = fecha_utc.replace(tzinfo=timezone.utc).astimezone(colombia_tz)
                fecha_str, hora_str = fecha_local.strftime('%d/%m/%Y'), fecha_local.strftime('%I:%M:%S %p')
            else: fecha_str, hora_str = str(acceso.fecha), ""
            
            equipo_text = acceso.equipos_str if acceso.equipos_str else 'Ninguno'
            cargo_text = usuario.cargo if usuario.cargo else (rol.nombre if rol else 'N/A')
            
            writer.writerow((usuario.documento or 'N/A', usuario.nombre or 'N/A', cargo_text, usuario.programa or 'N/A', usuario.ficha or 'N/A', equipo_text, acceso.tipo or 'N/A', fecha_str, hora_str))
            yield data.getvalue(); data.seek(0); data.truncate(0)

    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": f"attachment; filename=Auditoria_Accesos_{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"})
