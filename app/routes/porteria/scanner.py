from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import porteria_bp as bp
from ...models.usuarios import Usuario, avatar_de_cargo
from ...models.entidades import Visitante, Vehiculo, ObjetoExterno, Equipo
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
                # Siempre una URL valida: la foto real si existe, o el
                # avatar del cargo. Antes se devolvia None y el cliente caia a
                # ui-avatars.com, enviando el nombre real a un tercero.
                "foto": u.url_foto,
                # El celador tiene que saber si esa foto ya fue verificada por
                # un administrador: una foto sin aprobar no sirve para
                # confirmar la identidad de quien esta en la puerta.
                "foto_aprobada": bool(u.foto_aprobada),
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
                "foto": url_for('static', filename=avatar_de_cargo('visitante')),
                "cargo": "Visitante", "rol": "Externo", "tiempo_transcurrido": tiempo_transcurrido, "tiempo_excedido": tiempo_excedido
            }
    elif entity_type.startswith("Vehiculo"):
        veh = Vehiculo.query.filter_by(placa=real_id).first()
        if veh:
            is_inside = Acceso.query.filter_by(referencia_id=veh.id, tipo_referencia='Vehiculo').order_by(Acceso.fecha.desc()).first()
            data = {
                "found": True, "id": veh.id, "nombre": f"Vehículo {veh.placa}", "documento": veh.placa, "tipo": "Vehiculo",
                "foto": url_for('static', filename=avatar_de_cargo('vehiculo')),
                "status": is_inside.tipo if is_inside else 'Afuera', "cargo": veh.tipo, "rol": "Logística"
            }
    elif entity_type == "ObjetoExterno":
        obj = ObjetoExterno.query.filter_by(serial=real_id).first()
        if obj:
            is_inside = Acceso.query.filter_by(referencia_id=obj.id, tipo_referencia='ObjetoExterno').order_by(Acceso.fecha.desc()).first()
            data = {
                "found": True, "id": obj.id, "nombre": obj.descripcion, "documento": obj.serial, "tipo": "ObjetoExterno",
                "foto": url_for('static', filename=avatar_de_cargo('objetoexterno')),
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

MOVIMIENTOS_VALIDOS = ('Entrada', 'Salida')
ENTIDADES_VALIDAS = ('Usuario', 'Visitante', 'Vehiculo', 'ObjetoExterno')


def _estado_actual(referencia_id, tipo_referencia):
    """Devuelve 'Entrada' o 'Salida' segun el ultimo movimiento registrado."""
    ultimo = Acceso.query.filter_by(
        referencia_id=referencia_id, tipo_referencia=tipo_referencia
    ).order_by(Acceso.fecha.desc()).first()
    return ultimo.tipo if ultimo else 'Afuera'


def _auditar_discrepancia(referencia_id, tipo_referencia, movimiento, estado):
    """Registra una incoherencia de flujo. Devuelve el detalle o None."""
    if movimiento == 'Salida' and estado != 'Entrada':
        detalle = (f'Se forzo la salida de {tipo_referencia} ID {referencia_id} '
                   f'sin registro de entrada previo.')
    elif movimiento == 'Entrada' and estado == 'Entrada':
        detalle = (f'Se forzo la entrada de {tipo_referencia} ID {referencia_id} '
                   f'que ya figuraba adentro.')
    else:
        return None

    db.session.add(Auditoria(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        tabla_afectada='accesos',
        registro_id=referencia_id,
        accion='Inconsistencia de Acceso Detectada',
        autorizado_por=current_user.nombre,
        motivo='Registro de movimiento con inconsistencia de estado',
        detalles=detalle,
    ))
    return detalle


@bp.route('/register_movement/<int:user_id>/<type>', methods=['POST'])
@login_required
def register_movement(user_id, type):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not current_user.puede_operar_porteria:
        msg = 'No tienes permiso para registrar movimientos.'
        if is_ajax:
            return {"status": "error", "message": msg}, 403
        flash(msg, 'danger')
        return redirect(url_for('usuarios.profile'))

    if type not in MOVIMIENTOS_VALIDOS:
        msg = 'Tipo de movimiento no valido.'
        if is_ajax:
            return {"status": "error", "message": msg}, 400
        flash(msg, 'danger')
        return redirect(url_for('porteria.dashboard'))

    Usuario.query.get_or_404(user_id)

    try:
        # Este control existia para visitantes y vehiculos, pero no para
        # personas: se podian registrar dos entradas seguidas, o una salida
        # de alguien que nunca entro, sin dejar rastro.
        estado = _estado_actual(user_id, 'Usuario')
        detalle = _auditar_discrepancia(user_id, 'Usuario', type, estado)
        if detalle:
            db.session.commit()
            if is_ajax:
                return {"status": "error", "message": detalle}, 409
            flash(detalle, 'danger')
            return redirect(url_for('porteria.dashboard'))

        # Solo se aceptan equipos que pertenezcan a esa persona.
        equipos_ids = [i for i in request.form.getlist('equipos_ids') if i.isdigit()]
        equipos_propios = []
        if equipos_ids:
            equipos_propios = Equipo.query.filter(
                Equipo.usuario_id == user_id,
                Equipo.id.in_([int(i) for i in equipos_ids]),
            ).all()

        db.session.add(Acceso(
            punto_id=1,
            referencia_id=user_id,
            tipo_referencia='Usuario',
            tipo=type,
            equipos_str=','.join(str(e.id) for e in equipos_propios) or None,
            # Sin esto el historial de accesos no era atribuible a nadie.
            operador_id=current_user.id,
        ))

        if equipos_propios:
            nuevo_estado = 'Adentro' if type == 'Entrada' else 'Afuera'
            for equipo in equipos_propios:
                equipo.estado = nuevo_estado

        db.session.commit()
        msg = f'{type} registrada correctamente.'
        if is_ajax:
            return {"status": "success", "message": msg}
        flash(msg, 'success')
        return redirect(url_for('porteria.dashboard'))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error registrando el movimiento del usuario %s", user_id)
        msg = 'No se pudo registrar el movimiento.'
        if is_ajax:
            return {"status": "error", "message": msg}, 500
        flash(msg, 'danger')
        return redirect(url_for('porteria.dashboard'))


@bp.route('/register_movement_entidad/<tipo_entidad>/<int:entidad_id>/<mov>', methods=['POST'])
@login_required
def register_movement_entidad(tipo_entidad, entidad_id, mov):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403

    # Antes no se validaba nada: se podia insertar un Acceso con un tipo
    # inventado para una entidad inexistente, y esos registros contaminaban
    # los conteos de "adentro" del panel.
    if mov not in MOVIMIENTOS_VALIDOS or tipo_entidad not in ENTIDADES_VALIDAS:
        msg = 'Movimiento o tipo de entidad no valido.'
        if is_ajax:
            return {"status": "error", "message": msg}, 400
        flash(msg, 'danger')
        return redirect(url_for('porteria.dashboard'))

    # Las personas van por register_movement, que ademas registra los equipos.
    if tipo_entidad == 'Usuario':
        return register_movement(entidad_id, mov)

    modelos = {'Visitante': Visitante, 'Vehiculo': Vehiculo, 'ObjetoExterno': ObjetoExterno}
    if db.session.get(modelos[tipo_entidad], entidad_id) is None:
        msg = 'La entidad no existe.'
        if is_ajax:
            return {"status": "error", "message": msg}, 404
        flash(msg, 'danger')
        return redirect(url_for('porteria.dashboard'))

    try:
        estado = _estado_actual(entidad_id, tipo_entidad)
        detalle = _auditar_discrepancia(entidad_id, tipo_entidad, mov, estado)
        if detalle:
            db.session.commit()
            if is_ajax:
                return {"status": "error", "message": detalle}, 409
            flash(detalle, 'danger')
            return redirect(url_for('porteria.dashboard'))

        db.session.add(Acceso(punto_id=1, referencia_id=entidad_id,
                              tipo_referencia=tipo_entidad, tipo=mov,
                              operador_id=current_user.id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error registrando el movimiento de %s %s",
                                     tipo_entidad, entidad_id)
        msg = 'No se pudo registrar el movimiento.'
        if is_ajax:
            return {"status": "error", "message": msg}, 500
        flash(msg, 'danger')
        return redirect(url_for('porteria.dashboard'))

    msg = f'{mov} registrada correctamente.'
    if is_ajax:
        return {"status": "success", "message": msg,
                "redirect": url_for('porteria.dashboard')}
    flash(msg, 'success')
    return redirect(url_for('porteria.dashboard'))


@bp.route('/register_incidente', methods=['POST'])
@login_required
def register_incidente():
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    entidad_id = request.form.get('entidad_id')
    tipo_entidad = request.form.get('tipo_entidad') or 'Desconocido'
    detalles = request.form.get('detalles')
    if not detalles:
        flash('Detalles del incidente requeridos.', 'warning')
        return redirect(url_for('porteria.scanner'))
    # registro_id es una columna Integer no nula: antes se le pasaba la cadena
    # del formulario tal cual, y faltando tipo_entidad reventaba con un 500.
    db.session.add(Auditoria(
        usuario_id=current_user.id,
        nombre_usuario=current_user.nombre,
        tabla_afectada=tipo_entidad.lower() + 's',
        registro_id=int(entidad_id) if str(entidad_id).isdigit() else 0,
        accion='Incidente Registrado por Celador',
        autorizado_por=current_user.nombre,
        motivo='Reporte de anomalía o equipo no registrado',
        detalles=detalles
    ))
    db.session.commit()
    flash('Incidente registrado con éxito.', 'success')
    return redirect(url_for('porteria.scanner'))
