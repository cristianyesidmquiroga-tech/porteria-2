from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ...models.usuarios import Usuario
from ...models.asistencia import AsistenciaClase
from ... import db
from datetime import datetime, date
from . import bp


@bp.route('/comunicados')
@login_required
def comunicados():
    if not current_user.puede_gestionar_asistencia:
        flash('Acceso restringido. Solo Instructores o Administradores.', 'danger')
        return redirect(url_for('usuarios.profile'))

    usuarios = Usuario.query.filter(
        Usuario.correo != None,
        Usuario.correo_verificado == True
    ).order_by(Usuario.cargo, Usuario.nombre).all()

    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    from sqlalchemy import func
    inasistencias = db.session.query(
        AsistenciaClase.aprendiz_id,
        func.count(AsistenciaClase.id).label('total_faltas')
    ).filter(
        AsistenciaClase.presente == False,
        func.date(AsistenciaClase.fecha) >= inicio_mes
    ).group_by(AsistenciaClase.aprendiz_id).all()

    inasistentes = []
    for aprendiz_id, total_faltas in inasistencias:
        u = Usuario.query.get(aprendiz_id)
        if u and u.correo:
            inasistentes.append({
                'id': u.id,
                'nombre': u.nombre,
                'documento': u.documento or 'N/A',
                'correo': u.correo,
                'ficha': u.ficha or 'N/A',
                'programa': u.programa or 'N/A',
                'faltas': total_faltas
            })

    inasistentes.sort(key=lambda x: x['faltas'], reverse=True)

    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    mes_actual = f"{meses_es[hoy.month]} {hoy.year}"

    return render_template('usuarios/comunicados.html',
                           usuarios=usuarios,
                           inasistentes=inasistentes,
                           mes_actual=mes_actual)


@bp.route('/api/enviar_comunicado', methods=['POST'])
@login_required
def api_enviar_comunicado():
    if not current_user.puede_gestionar_asistencia:
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    from app.utils.email import enviar_correo

    data = request.json
    tipo = data.get('tipo', 'Comunicado General')
    mensaje_personalizado = data.get('mensaje', '').strip()
    destinatarios_ids = data.get('destinatarios', [])

    if not destinatarios_ids:
        return jsonify({"status": "error", "message": "No se seleccionaron destinatarios"}), 400

    tipo_color = {
        'Llegada tarde': '#e67e22',
        'Llamado de atención': '#e74c3c',
        'Uniforme incorrecto': '#8e44ad',
        'Inasistencias': '#c0392b',
    }.get(tipo, '#2c3e50')

    fecha_str = datetime.now().strftime('%d/%m/%Y a las %I:%M %p')
    remitente_nombre = current_user.nombre
    remitente_cargo = current_user.cargo or 'Instructor'

    enviados = 0
    errores = []

    for uid in destinatarios_ids:
        try:
            u = Usuario.query.get(int(uid))
            if not u or not u.correo:
                continue

            # Obtener datos de inasistencias si aplica
            faltas_txt = ''
            if tipo == 'Inasistencias':
                hoy = date.today()
                inicio_mes = hoy.replace(day=1)
                from sqlalchemy import func
                total_faltas = db.session.query(func.count(AsistenciaClase.id)).filter(
                    AsistenciaClase.aprendiz_id == u.id,
                    AsistenciaClase.presente == False,
                    func.date(AsistenciaClase.fecha) >= inicio_mes
                ).scalar() or 0
                if total_faltas:
                    faltas_txt = f"""
                    <div style="background:#fff3cd;border-left:4px solid #f39c12;padding:12px 16px;border-radius:6px;margin:16px 0;">
                        <strong>Inasistencias registradas este mes:</strong>
                        <span style="font-size:1.5rem;font-weight:900;color:#c0392b;margin-left:8px;">{total_faltas}</span>
                    </div>"""

            asunto = f"Comunicado SENA - {tipo}"
            cuerpo = f"""
<div style="font-family:Arial,sans-serif;color:#333;max-width:640px;margin:0 auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;background:#fff;">
  <div style="background:{tipo_color};padding:24px;text-align:center;">
    <h2 style="color:#fff;margin:0;font-size:1.4rem;">SENA - Centro de Gestión Agroempresarial del Oriente</h2>
    <p style="color:rgba(255,255,255,0.9);margin:6px 0 0;font-size:0.95rem;">Vélez, Santander</p>
  </div>
  <div style="padding:28px;">
    <div style="display:inline-block;background:{tipo_color}22;border:1px solid {tipo_color};color:{tipo_color};padding:6px 14px;border-radius:20px;font-size:0.85rem;font-weight:700;margin-bottom:16px;">
      {tipo.upper()}
    </div>
    <h3 style="margin-top:0;">Estimado/a {u.nombre},</h3>
    <p>Le informamos que ha sido registrado(a) un <strong>{tipo}</strong> en el Sistema de Acceso SENA el día <strong>{fecha_str}</strong>.</p>
    {faltas_txt}
    {f'<div style="background:#f8f9fa;border-left:4px solid {tipo_color};padding:14px 16px;border-radius:6px;margin:16px 0;"><strong>Observación:</strong><br>{mensaje_personalizado}</div>' if mensaje_personalizado else ''}
    <p>Le solicitamos atender el presente comunicado y tomar las medidas correspondientes a la brevedad posible.</p>
    <p>Si considera que este comunicado es un error, por favor comuníquese directamente con:</p>
    <div style="background:#f1f1f1;padding:12px 16px;border-radius:6px;margin:16px 0;">
      <strong>{remitente_nombre}</strong> — {remitente_cargo}<br>
      <span style="color:#555;font-size:0.9rem;">Centro de Gestión Agroempresarial del Oriente - SENA Vélez</span>
    </div>
    <div style="background:#f9f9f9;border-left:4px solid #39A900;padding:12px;margin-top:20px;font-size:13px;color:#555;">
      <strong>Política de privacidad:</strong> Este comunicado es de uso exclusivo del Sistema de Acceso SENA y se emite conforme a las políticas institucionales de convivencia y reglamento interno.
    </div>
  </div>
  <div style="background:#f4f4f4;padding:16px;text-align:center;font-size:12px;color:#777;">
    <p style="margin:0;">Correo generado automáticamente — No responda a este mensaje.</p>
  </div>
</div>"""

            result = enviar_correo(u.correo, asunto, cuerpo)
            if result is not False:
                enviados += 1
            else:
                errores.append(u.nombre)
        except Exception as e:
            errores.append(str(e))

    return jsonify({
        "status": "success",
        "message": f"Comunicado enviado a {enviados} destinatario(s).",
        "enviados": enviados,
        "errores": errores
    })
