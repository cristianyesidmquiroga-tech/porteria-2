from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import porteria_bp as bp
from ...models.usuarios import Usuario
from ...models.entidades import Visitante, Vehiculo
from ...models.accesos import Acceso
from ... import db

@bp.route('/scanner')
@login_required
def scanner():
    if not current_user.puede_operar_porteria:
        flash('Solo el personal de portería o administradores pueden usar el escáner.', 'danger')
        return redirect(url_for('usuarios.profile'))
    return render_template('porteria/scanner.html')

@bp.route('/api/verify/<doc>')
@login_required
def api_verify(doc):
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    
    entity_type, real_id = "Usuario", doc
    if doc.startswith("SENA-VISIT:"): entity_type, real_id = "Visitante", doc.replace("SENA-VISIT:", "")
    elif doc.startswith("SENA-VEH-S:"): entity_type, real_id = "Vehiculo-S", doc.replace("SENA-VEH-S:", "")
    elif doc.startswith("SENA-VEH-E:"): entity_type, real_id = "Vehiculo-E", doc.replace("SENA-VEH-E:", "")
    elif doc.startswith("SENA-CARNET:"): entity_type, real_id = "Usuario", doc.replace("SENA-CARNET:", "")

    data = {"found": False}
    if entity_type == "Usuario":
        u = Usuario.query.filter_by(documento=real_id).first()
        if u:
            is_inside = Acceso.query.filter_by(referencia_id=u.id, tipo_referencia='Usuario').order_by(Acceso.fecha.desc()).first()
            equipos_list = [{"id": e.id, "nombre": e.nombre, "tipo": e.tipo, "serial": e.serial, "estado": e.estado} for e in u.equipos]
            data = {
                "found": True, "id": u.id, "nombre": u.nombre, "documento": u.documento, "cargo": u.cargo, "rol": u.rol.nombre if u.rol else 'N/A',
                "tipo": "Usuario", "status": is_inside.tipo if is_inside else 'Afuera',
                "foto": url_for('static', filename='uploads/profiles/' + u.foto) if u.foto else None,
                "equipos": equipos_list
            }
    elif entity_type == "Visitante":
        v = Visitante.query.filter_by(documento=real_id).first()
        if v:
            is_inside = Acceso.query.filter_by(referencia_id=v.id, tipo_referencia='Visitante').order_by(Acceso.fecha.desc()).first()
            data = {
                "found": True, "id": v.id, "nombre": v.nombre, "documento": v.documento, "tipo": "Visitante", "status": is_inside.tipo if is_inside else 'Afuera'
            }
    # (Similar para vehículos si es necesario, por ahora priorizamos Usuario/Visitante)
    
    return data

@bp.route('/verify/<doc>')
@login_required
def verify(doc):
    if not current_user.puede_operar_porteria:
        flash('Acceso denegado. Solo el personal autorizado puede verificar documentos.', 'danger')
        return redirect(url_for('usuarios.profile'))

    entity_type, real_id = "Usuario", doc
    if doc.startswith("SENA-VISIT:"): entity_type, real_id = "Visitante", doc.replace("SENA-VISIT:", "")
    elif doc.startswith("SENA-VEH-S:"): entity_type, real_id = "Vehiculo-S", doc.replace("SENA-VEH-S:", "")
    elif doc.startswith("SENA-VEH-E:"): entity_type, real_id = "Vehiculo-E", doc.replace("SENA-VEH-E:", "")
    elif doc.startswith("SENA-CARNET:"): entity_type, real_id = "Usuario", doc.replace("SENA-CARNET:", "")

    if entity_type == "Usuario":
        user = Usuario.query.filter_by(documento=real_id).first()
        if not user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('porteria.scanner'))
        is_inside = Acceso.query.filter_by(referencia_id=user.id, tipo_referencia='Usuario').order_by(Acceso.fecha.desc()).first()
        status = is_inside.tipo if is_inside else 'Afuera'
        return render_template('porteria/verify.html', user_profile=user, status=status)

    elif entity_type == "Visitante":
        visitante = Visitante.query.filter_by(documento=real_id).first()
        if not visitante:
            flash('Visitante no encontrado.', 'danger')
            return redirect(url_for('porteria.scanner'))
        is_inside = Acceso.query.filter_by(referencia_id=visitante.id, tipo_referencia='Visitante').order_by(Acceso.fecha.desc()).first()
        status = is_inside.tipo if is_inside else 'Afuera'
        return render_template('porteria/verify_entidad.html', entidad=visitante, tipo='Visitante', status=status)

    elif entity_type.startswith("Vehiculo"):
        vehiculo = Vehiculo.query.filter_by(placa=real_id).first()
        if not vehiculo:
            flash('Vehículo no encontrado.', 'danger')
            return redirect(url_for('porteria.scanner'))
        is_inside = Acceso.query.filter_by(referencia_id=vehiculo.id, tipo_referencia='Vehiculo').order_by(Acceso.fecha.desc()).first()
        status = is_inside.tipo if is_inside else 'Afuera'
        return render_template('porteria/verify_entidad.html', entidad=vehiculo, tipo='Vehiculo', status=status)

    return redirect(url_for('porteria.scanner'))

@bp.route('/register_movement_entidad/<tipo_entidad>/<int:entidad_id>/<mov>', methods=['POST'])
@login_required
def register_movement_entidad(tipo_entidad, entidad_id, mov):
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    db.session.add(Acceso(punto_id=1, referencia_id=entidad_id, tipo_referencia=tipo_entidad, tipo=mov))
    db.session.commit()
    msg = f'{mov} registrada correctamente.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": msg, "redirect": url_for('porteria.dashboard')}
    flash(msg, 'success')
    return redirect(url_for('porteria.dashboard'))

@bp.route('/register_movement/<int:user_id>/<type>', methods=['POST'])
@login_required
def register_movement(user_id, type):
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    user = Usuario.query.get(user_id)
    if not user: return {"error": "User not found"}, 404
    equipos_ids = request.form.getlist('equipos_ids')
    nombres_equipos = []
    for equipo in user.equipos:
        if str(equipo.id) in equipos_ids:
            equipo.estado = 'Adentro' if type == 'Entrada' else 'Afuera'
            nombres_equipos.append(equipo.nombre)
    
    nuevo_acceso = Acceso(punto_id=1, referencia_id=user.id, tipo_referencia='Usuario', tipo=type)
    if nombres_equipos:
        nuevo_acceso.equipos_str = ", ".join(nombres_equipos)
    
    db.session.add(nuevo_acceso)
    db.session.commit()
    msg = f'{type} registrada para {user.nombre}.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": msg, "redirect": url_for('porteria.dashboard')}
    flash(msg, 'success')
    return redirect(url_for('porteria.dashboard'))
