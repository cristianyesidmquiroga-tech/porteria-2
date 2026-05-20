from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import porteria_bp as bp
from ...models.usuarios import Usuario
from ...models.entidades import Visitante, Vehiculo, ObjetoExterno
from ...models.accesos import Acceso, Auditoria
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
    elif doc.startswith("SENA-OBJ:"): entity_type, real_id = "ObjetoExterno", doc.replace("SENA-OBJ:", "")

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
            status = is_inside.tipo if is_inside else 'Afuera'
            
            tiempo_transcurrido = None
            tiempo_excedido = False
            if status == 'Entrada' and is_inside:
                from app.utils import get_colombia_time
                now_local = get_colombia_time()
                fecha_acceso = is_inside.fecha
                if isinstance(fecha_acceso, str):
                    from datetime import datetime
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                        try: fecha_acceso = datetime.strptime(fecha_acceso, fmt); break
                        except ValueError: continue
                diff = now_local - fecha_acceso
                diff_seconds = diff.total_seconds()
                if diff_seconds > 0:
                    horas = int(diff_seconds // 3600)
                    minutos = int((diff_seconds % 3600) // 60)
                    tiempo_transcurrido = f"{horas}h {minutos}m"
                    if diff_seconds > 7200:
                        tiempo_excedido = True
                        
            data = {
                "found": True, "id": v.id, "nombre": v.nombre, "documento": v.documento, "tipo": "Visitante", "status": status,
                "cargo": "Visitante", "rol": "Externo", "tiempo_transcurrido": tiempo_transcurrido, "tiempo_excedido": tiempo_excedido
            }
    elif entity_type.startswith("Vehiculo"):
        veh = Vehiculo.query.filter_by(placa=real_id).first()
        if veh:
            is_inside = Acceso.query.filter_by(referencia_id=veh.id, tipo_referencia='Vehiculo').order_by(Acceso.fecha.desc()).first()
            data = {
                "found": True, "id": veh.id, "nombre": f"Vehículo {veh.placa}", "documento": veh.placa, "tipo": "Vehiculo",
                "status": is_inside.tipo if is_inside else 'Afuera', "cargo": veh.tipo, "rol": "Logística"
            }
    elif entity_type == "ObjetoExterno":
        obj = ObjetoExterno.query.filter_by(serial=real_id).first()
        if obj:
            is_inside = Acceso.query.filter_by(referencia_id=obj.id, tipo_referencia='ObjetoExterno').order_by(Acceso.fecha.desc()).first()
            data = {
                "found": True, "id": obj.id, "nombre": obj.descripcion, "documento": obj.serial, "tipo": "ObjetoExterno",
                "status": is_inside.tipo if is_inside else 'Afuera', "cargo": obj.propietario or "Externo", "rol": "Equipo de Tercero"
            }
    
    return data

@bp.route('/verify/<doc>')
@login_required
def verify(doc):
    if not current_user.puede_operar_porteria:
        flash('Acceso denegado. Solo el personal de portería autorizado puede verificar documentos.', 'danger')
        return redirect(url_for('usuarios.profile'))

    entity_type, real_id = "Usuario", doc
    if doc.startswith("SENA-VISIT:"): entity_type, real_id = "Visitante", doc.replace("SENA-VISIT:", "")
    elif doc.startswith("SENA-VEH-S:"): entity_type, real_id = "Vehiculo-S", doc.replace("SENA-VEH-S:", "")
    elif doc.startswith("SENA-VEH-E:"): entity_type, real_id = "Vehiculo-E", doc.replace("SENA-VEH-E:", "")
    elif doc.startswith("SENA-CARNET:"): entity_type, real_id = "Usuario", doc.replace("SENA-CARNET:", "")
    elif doc.startswith("SENA-OBJ:"): entity_type, real_id = "ObjetoExterno", doc.replace("SENA-OBJ:", "")

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
        
        tiempo_transcurrido = None
        tiempo_excedido = False
        if status == 'Entrada' and is_inside:
            from app.utils import get_colombia_time
            now_local = get_colombia_time()
            fecha_acceso = is_inside.fecha
            if isinstance(fecha_acceso, str):
                from datetime import datetime
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                    try: fecha_acceso = datetime.strptime(fecha_acceso, fmt); break
                    except ValueError: continue
            diff = now_local - fecha_acceso
            diff_seconds = diff.total_seconds()
            if diff_seconds > 0:
                horas = int(diff_seconds // 3600)
                minutos = int((diff_seconds % 3600) // 60)
                tiempo_transcurrido = f"{horas}h {minutos}m"
                if diff_seconds > 7200:
                    tiempo_excedido = True

        return render_template('porteria/verify_entidad.html', entidad=visitante, tipo='Visitante', status=status, tiempo_transcurrido=tiempo_transcurrido, tiempo_excedido=tiempo_excedido)

    elif entity_type.startswith("Vehiculo"):
        vehiculo = Vehiculo.query.filter_by(placa=real_id).first()
        if not vehiculo:
            flash('Vehículo no encontrado.', 'danger')
            return redirect(url_for('porteria.scanner'))
        is_inside = Acceso.query.filter_by(referencia_id=vehiculo.id, tipo_referencia='Vehiculo').order_by(Acceso.fecha.desc()).first()
        status = is_inside.tipo if is_inside else 'Afuera'
        return render_template('porteria/verify_entidad.html', entidad=vehiculo, tipo='Vehiculo', status=status)

    elif entity_type == "ObjetoExterno":
        objeto = ObjetoExterno.query.filter_by(serial=real_id).first()
        if not objeto:
            flash('Objeto externo no encontrado.', 'danger')
            return redirect(url_for('porteria.scanner'))
        is_inside = Acceso.query.filter_by(referencia_id=objeto.id, tipo_referencia='ObjetoExterno').order_by(Acceso.fecha.desc()).first()
        status = is_inside.tipo if is_inside else 'Afuera'
        return render_template('porteria/verify_entidad.html', entidad=objeto, tipo='ObjetoExterno', status=status)

    return redirect(url_for('porteria.scanner'))

@bp.route('/register_movement_entidad/<tipo_entidad>/<int:entidad_id>/<mov>', methods=['POST'])
@login_required
def register_movement_entidad(tipo_entidad, entidad_id, mov):
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    
    is_inside = Acceso.query.filter_by(referencia_id=entidad_id, tipo_referencia=tipo_entidad).order_by(Acceso.fecha.desc()).first()
    status_actual = is_inside.tipo if is_inside else 'Afuera'
    
    discrepancia = False
    if mov == 'Salida' and status_actual != 'Entrada':
        discrepancia = True
        detalles_disc = f'El celador forzó la salida de {tipo_entidad} ID {entidad_id} sin registro de entrada previo.'
    elif mov == 'Entrada' and status_actual == 'Entrada':
        discrepancia = True
        detalles_disc = f'El celador forzó la entrada de {tipo_entidad} ID {entidad_id} que ya figuraba adentro.'
        
    if discrepancia:
        db.session.add(Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='accesos',
            registro_id=entidad_id,
            accion='Inconsistencia de Acceso Detectada',
            autorizado_por=current_user.nombre,
            motivo='Registro de movimiento con inconsistencia de estado',
            detalles=detalles_disc
        ))
    
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
    
    is_inside = Acceso.query.filter_by(referencia_id=user.id, tipo_referencia='Usuario').order_by(Acceso.fecha.desc()).first()
    status_actual = is_inside.tipo if is_inside else 'Afuera'
    
    discrepancia = False
    if type == 'Salida' and status_actual != 'Entrada':
        discrepancia = True
        detalles_disc = f'El celador forzó la salida de Usuario {user.nombre} ({user.documento}) sin registro de entrada previo.'
    elif type == 'Entrada' and status_actual == 'Entrada':
        discrepancia = True
        detalles_disc = f'El celador forzó la entrada de Usuario {user.nombre} ({user.documento}) que ya figuraba adentro.'
        
    if discrepancia:
        db.session.add(Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='usuarios',
            registro_id=user.id,
            accion='Inconsistencia de Acceso Detectada',
            autorizado_por=current_user.nombre,
            motivo='Registro de movimiento con inconsistencia de estado',
            detalles=detalles_disc
        ))
    
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

@bp.route('/register_incidente', methods=['POST'])
@login_required
def register_incidente():
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    entidad_id = request.form.get('entidad_id')
    tipo_entidad = request.form.get('tipo_entidad')
    detalles = request.form.get('detalles')
    
    if not detalles:
        flash('Detalles del incidente requeridos.', 'warning')
        return redirect(url_for('porteria.scanner'))
        
    db.session.add(Auditoria(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        tabla_afectada=tipo_entidad.lower() + 's',
        registro_id=entidad_id,
        accion='Incidente Registrado por Celador',
        autorizado_por=current_user.nombre,
        motivo='Reporte de anomalía o equipo no registrado',
        detalles=detalles
    ))
    db.session.commit()
    flash('Incidente registrado con éxito.', 'success')
    return redirect(url_for('porteria.scanner'))
