from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from ...models.usuarios import Usuario, Rol, TurnoCelador
from ... import db
from . import bp
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# Decorador o chequeo simple para asegurar admin
def check_admin():
    if not current_user.es_admin:
        return False
    return True

@bp.route('/admin_gestion', methods=['GET'])
@login_required
def admin_gestion():
    if not check_admin():
        flash("Acceso denegado. Área exclusiva para administradores.", "danger")
        return redirect(url_for('main.index'))
    
    # Obtener todos los roles y usuarios
    roles = Rol.query.all()
    usuarios = Usuario.query.order_by(Usuario.id.desc()).all()
    
    return render_template('usuarios/gestion.html', usuarios=usuarios, roles=roles)

@bp.route('/admin/descargar_respaldo/<filename>')
@login_required
def descargar_respaldo(filename):
    if not check_admin():
        flash("Acceso denegado.", "danger")
        return redirect(url_for('main.index'))
    
    import os
    from flask import current_app, send_from_directory
    respaldos_dir = os.path.join(current_app.root_path, 'respaldos_mensuales')
    return send_from_directory(respaldos_dir, filename, as_attachment=True)

@bp.route('/admin/respaldos')
@login_required
def admin_respaldos():
    if not check_admin():
        flash("Acceso denegado.", "danger")
        return redirect(url_for('main.index'))
    
    import os
    from flask import current_app
    respaldos_dir = os.path.join(current_app.root_path, 'respaldos_mensuales')
    respaldos_archivos = []
    if os.path.exists(respaldos_dir):
        respaldos_archivos = sorted(os.listdir(respaldos_dir), reverse=True)
        
    return render_template('usuarios/respaldos.html', respaldos=respaldos_archivos)

@bp.route('/api/admin/crear_usuario', methods=['POST'])
@login_required
def api_crear_usuario():
    if not check_admin():
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.json
    try:
        # Validaciones básicas
        if not data.get('nombre') or not data.get('correo') or not data.get('contraseña') or not data.get('rol_id'):
            return jsonify({"status": "error", "message": "Faltan datos obligatorios"}), 400

        # Verificar existencia
        if Usuario.query.filter_by(correo=data['correo']).first():
            return jsonify({"status": "error", "message": "El correo ya está registrado"}), 400
        if data.get('documento') and Usuario.query.filter_by(documento=data['documento']).first():
            return jsonify({"status": "error", "message": "El documento ya está registrado"}), 400

        from app.utils.email import enviar_correo
        from app.models.usuarios import Rol
        
        rol = Rol.query.get(int(data['rol_id']))
        es_usuario_normal = rol and rol.nombre == 'Usuario'

        nuevo_usuario = Usuario(
            nombre=data['nombre'],
            correo=data['correo'].lower(),
            documento=data.get('documento'),
            rol_id=int(data['rol_id']),
            cargo=data.get('cargo'),
            ficha=data.get('ficha'),
            programa=data.get('programa'),
            horario=data.get('horario'),
            perfil_completo=False if es_usuario_normal else True,
            correo_verificado=data.get('verificado', False),
            debe_cambiar_contrasena=es_usuario_normal
        )
        nuevo_usuario.set_password(data['contraseña'])
        
        db.session.add(nuevo_usuario)
        db.session.flush() # Para obtener el ID

        # Si el cargo es Celador, creamos un turno
        if nuevo_usuario.cargo == 'Celador':
            turno = TurnoCelador(celador_id=nuevo_usuario.id, estado='Activo')
            db.session.add(turno)

        # Send Email
        if es_usuario_normal:
            asunto = "Bienvenido al Sistema de Acceso - SENA Vélez Santander"
            link_login = url_for('auth.login', _external=True)
            cuerpo_html = f"""
            <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #39A900; padding: 20px; text-align: center;">
                    <h2 style="color: white; margin: 0;">SENA - Regional Santander</h2>
                    <p style="color: white; margin: 5px 0 0 0;">Centro de Gestión Agroempresarial del Oriente (Vélez)</p>
                </div>
                <div style="padding: 20px;">
                    <h3>Hola, {data['nombre']}</h3>
                    <p>Se te ha creado un perfil institucional para el ingreso a la plataforma de gestión de accesos.</p>
                    <p>Estas son tus credenciales de acceso temporal:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <p style="margin: 5px 0;"><strong>Usuario/Correo:</strong> {data['correo'].lower()}</p>
                        <p style="margin: 5px 0;"><strong>Contraseña:</strong> {data['contraseña']}</p>
                    </div>
                    
                    <h4 style="color: #e74c3c;">¡IMPORTANTE! Instrucciones Obligatorias:</h4>
                    <ol>
                        <li>Ingresa a la plataforma a través del siguiente enlace: <a href="{link_login}" style="color: #39A900; font-weight: bold;">Ingresar al Sistema</a>.</li>
                        <li>Apenas ingreses, el sistema te exigirá <strong>cambiar tu contraseña temporal</strong> por una propia y segura.</li>
                        <li>Una vez cambiada, deberás dirigirte a tu <strong>Perfil</strong> y diligenciar toda tu información personal.</li>
                        <li><strong>Código QR:</strong> Solo cuando tu perfil esté 100% completo, se activará tu código QR, el cual es necesario para poder entrar y salir de la institución.</li>
                        <li><strong>Registro de Equipos:</strong> Si vas a ingresar con dispositivos (como computadores portátiles), debes registrarlos previamente en tu perfil usando el número de serie (S/N) y el nombre del equipo.</li>
                    </ol>
                    <p style="color: #e74c3c; font-weight: bold; text-align: center; margin-top: 30px;">
                        ⚠️ Si no realizas este proceso, NO podrás ingresar a la institución.
                    </p>
                </div>
                <div style="background-color: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                    <p>Este es un correo generado automáticamente, por favor no respondas a este mensaje.</p>
                </div>
            </div>
            """
            enviar_correo(data['correo'].lower(), asunto, cuerpo_html)



        db.session.commit()
        return jsonify({"status": "success", "message": "Usuario creado exitosamente"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/admin/editar_usuario/<int:id>', methods=['PUT'])
@login_required
def api_editar_usuario(id):
    if not check_admin():
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.json
    usuario = Usuario.query.get_or_404(id)

    try:
        from app.models.accesos import Auditoria
        # Actualizar datos básicos
        if 'nombre' in data: usuario.nombre = data['nombre']
        if 'documento' in data: usuario.documento = data['documento']
        if 'cargo' in data: usuario.cargo = data['cargo']
        if 'rol_id' in data: usuario.rol_id = int(data['rol_id'])
        if 'ficha' in data: usuario.ficha = data['ficha']
        if 'programa' in data: usuario.programa = data['programa']
        if 'horario' in data: usuario.horario = data['horario']
        
        if 'verificado' in data: 
            usuario.correo_verificado = data['verificado']
            
        if 'estado_bloqueo' in data:
            if data['estado_bloqueo'] == 'desbloquear':
                usuario.bloqueado_hasta = None
                usuario.intentos_fallidos = 0
            
        if 'contraseña' in data and data['contraseña'].strip():
            usuario.set_password(data['contraseña'])

        # Registro de Auditoría Obligatorio
        nueva_auditoria = Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='usuarios',
            registro_id=id,
            accion='Edición de Perfil',
            autorizado_por=data.get('autorizado_por'),
            motivo=data.get('motivo'),
            detalles=f"Edición de datos del perfil: {usuario.nombre} ({usuario.correo})"
        )
        db.session.add(nueva_auditoria)
        db.session.commit()
        return jsonify({"status": "success", "message": "Usuario actualizado y cambio registrado exitosamente"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/admin/eliminar_usuario/<int:id>', methods=['DELETE'])
@login_required
def api_eliminar_usuario(id):
    if not check_admin():
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.json or {}
    # Evitar que el admin se elimine a sí mismo
    if current_user.id == id:
        return jsonify({"status": "error", "message": "No puedes eliminar tu propia cuenta"}), 400

    usuario = Usuario.query.get_or_404(id)
    info_usuario = f"{usuario.nombre} ({usuario.correo})"
    
    if usuario.rol and usuario.rol.nombre == 'Admin':
        return jsonify({"status": "error", "message": "No se pueden eliminar cuentas con rol de Administrador. Solo se permite su edición."}), 403

    try:
        from app.models.entidades import Equipo
        from app.models.usuarios import Carnet, CodigoQR, TurnoCelador
        from app.models.accesos import Acceso, Auditoria
        from app.models.movimientos import MovimientoEquipo

        # 1. Eliminar Auditoría antigua de este usuario (como registro afectado)
        # Auditoria.query.filter_by(usuario_id=id).delete() # No, esto borraría lo que ÉL hizo.
        # Mejor no borrar auditorías antiguas, solo dependencias técnicas.

        # 2. Eliminar Turnos de Celador
        TurnoCelador.query.filter_by(celador_id=id).delete()

        # 3. Eliminar Equipos y sus movimientos
        equipos = Equipo.query.filter_by(usuario_id=id).all()
        for e in equipos:
            MovimientoEquipo.query.filter_by(equipo_id=e.id).delete()
            db.session.delete(e)

        # 4. Eliminar Carnet, sus códigos QR y accesos asociados
        carnet = Carnet.query.filter_by(usuario_id=id).first()
        if carnet:
            CodigoQR.query.filter_by(carnet_id=carnet.id).delete()
            Acceso.query.filter_by(carnet_id=carnet.id).delete()
            db.session.delete(carnet)
            
        # 5. Eliminar Accesos directos por referencia
        Acceso.query.filter_by(referencia_id=id, tipo_referencia='Usuario').delete()

        # 6. Registro de Auditoría de Eliminación (Antes de borrar al usuario para que current_user sea válido)
        nueva_auditoria = Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='usuarios',
            registro_id=id,
            accion='Eliminación Permanente',
            autorizado_por=data.get('autorizado_por'),
            motivo=data.get('motivo'),
            detalles=f"Eliminación total del perfil: {info_usuario}"
        )
        db.session.add(nueva_auditoria)

        # 7. Finalmente, eliminar el usuario
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"status": "success", "message": "Usuario eliminado y acción registrada en el historial"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error al eliminar: {str(e)}"}), 500

@bp.route('/admin_historial')
@login_required
def admin_historial():
    if not check_admin():
        flash("Acceso denegado.", "danger")
        return redirect(url_for('main.index'))
    
    from app.models.accesos import Auditoria
    # Obtener logs de auditoría ordenados por fecha descendente
    logs = Auditoria.query.order_by(Auditoria.fecha.desc()).all()
    return render_template('usuarios/historial.html', logs=logs)
