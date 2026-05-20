from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import porteria_bp as bp
from ...models.entidades import Visitante, Vehiculo, ObjetoExterno
from ... import db

@bp.route('/pases')
@login_required
def pases():
    if not current_user.puede_operar_porteria:
        flash('No tienes permiso.', 'danger')
        return redirect(url_for('usuarios.profile'))
    visitantes = Visitante.query.order_by(Visitante.fecha_creacion.desc()).all()
    vehiculos = Vehiculo.query.all()
    objetos = ObjetoExterno.query.order_by(ObjetoExterno.fecha_creacion.desc()).all()
    return render_template('porteria/pases.html', visitantes=visitantes, vehiculos=vehiculos, objetos=objetos)

@bp.route('/pases/crear_visitante', methods=['POST'])
@login_required
def crear_visitante():
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    nombre, documento, motivo = request.form.get('nombre'), request.form.get('documento'), request.form.get('motivo')
    if not nombre or not documento:
        flash('Nombre y documento requeridos.', 'warning')
        return redirect(url_for('porteria.pases'))
    visit_exist = Visitante.query.filter_by(documento=documento).first()
    if visit_exist:
        visit_exist.nombre, visit_exist.motivo, visit_exist.activo = nombre, motivo, True
    else:
        db.session.add(Visitante(nombre=nombre, documento=documento, motivo=motivo, qr_code=f"SENA-VISIT:{documento}"))
    db.session.commit()
    msg = 'Visitante registrado con éxito.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": msg, "reload": True}
    flash(msg, 'success')
    return redirect(url_for('porteria.pases'))

@bp.route('/pases/crear_vehiculo', methods=['POST'])
@login_required
def crear_vehiculo():
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    placa, tipo, propietario, motivo = request.form.get('placa').upper(), request.form.get('tipo'), request.form.get('propietario'), request.form.get('motivo')
    if not placa:
        flash('La placa es requerida.', 'warning')
        return redirect(url_for('porteria.pases'))
    veh_exist = Vehiculo.query.filter_by(placa=placa).first()
    prefix = "SENA-VEH-S" if tipo == 'SENA' else "SENA-VEH-E"
    if veh_exist:
        veh_exist.tipo, veh_exist.propietario, veh_exist.motivo, veh_exist.activo = tipo, propietario, motivo, True
    else:
        db.session.add(Vehiculo(placa=placa, tipo=tipo, propietario=propietario, motivo=motivo, qr_code=f"{prefix}:{placa}"))
    db.session.commit()
    msg = 'Vehículo registrado con éxito.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": msg, "reload": True}
    flash(msg, 'success')
    return redirect(url_for('porteria.pases'))

@bp.route('/pases/crear_objeto', methods=['POST'])
@login_required
def crear_objeto():
    if not current_user.puede_operar_porteria:
        return {"error": "Unauthorized"}, 403
    descripcion = request.form.get('descripcion')
    serial = request.form.get('serial')
    propietario = request.form.get('propietario')
    motivo = request.form.get('motivo')

    if not descripcion:
        flash('La descripción es requerida.', 'warning')
        return redirect(url_for('porteria.pases'))

    obj_exist = None
    if serial:
        obj_exist = ObjetoExterno.query.filter_by(serial=serial).first()

    if obj_exist:
        obj_exist.descripcion = descripcion
        obj_exist.propietario = propietario
        obj_exist.motivo = motivo
        obj_exist.activo = True
    else:
        from datetime import datetime
        serial_val = serial if serial else f"SN-{int(datetime.utcnow().timestamp())}"
        # Si el serial generado ya existe por casualidad, intentamos con milisegundos
        while ObjetoExterno.query.filter_by(serial=serial_val).first():
            import time
            time.sleep(0.01)
            serial_val = f"SN-{int(time.time() * 100)}"
            
        db.session.add(ObjetoExterno(
            descripcion=descripcion,
            serial=serial_val,
            propietario=propietario,
            motivo=motivo,
            qr_code=f"SENA-OBJ:{serial_val}",
            activo=True
        ))
    db.session.commit()
    msg = 'Objeto externo registrado con éxito.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": msg, "reload": True}
    flash(msg, 'success')
    return redirect(url_for('porteria.pases'))

