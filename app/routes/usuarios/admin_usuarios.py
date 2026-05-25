from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from ...models.usuarios import Usuario, Rol, TurnoCelador
from ... import db
from . import bp
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
import pandas as pd
import io

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
            <div style="font-family: Arial, sans-serif; color: #333333; max-width: 680px; margin: 0 auto; border: 1px solid #dddddd; border-radius: 10px; overflow: hidden; background-color: #ffffff;">
                <div style="background-color: #ffffff; padding: 24px 24px 16px 24px; text-align: center; border-bottom: 5px solid #39A900;">
                    <div style="font-size: 44px; font-weight: 900; color: #39A900; letter-spacing: 1px; line-height: 1;">SENA</div>
                    <h2 style="color: #39A900; margin: 12px 0 4px 0;">SENA Vélez Santander</h2>
                    <p style="color: #555555; margin: 0;">Sistema de Acceso y Carnet Digital</p>
                </div>
                <div style="padding: 26px;">
                    <h3>Hola, {data['nombre']}</h3>
                    <p>Somos del <strong>SENA Vélez</strong> y te comunicamos que, para el ingreso a nuestra institución por portería, debes contar con un <strong>carnet digital activo</strong>.</p>
                    <p>Para iniciar el proceso, ingresa a la plataforma desde el siguiente enlace:</p>
                    <p style="text-align: center; margin: 26px 0;">
                        <a href="{link_login}" style="background-color: #39A900; color: #ffffff; padding: 13px 24px; text-decoration: none; border-radius: 7px; font-weight: bold; display: inline-block;">Ingresar a la plataforma</a>
                    </p>
                    <p>Si el botón no funciona, copia y pega esta URL en tu navegador:</p>
                    <p style="word-break: break-all;"><a href="{link_login}" style="color: #39A900;">{link_login}</a></p>
                    <p>Estas son tus credenciales de acceso temporal:</p>
                    <div style="background-color: #f5f5f5; padding: 16px; border-radius: 7px; margin-bottom: 22px; border-left: 4px solid #39A900;">
                        <p style="margin: 6px 0;"><strong>Usuario:</strong> {data['correo'].lower()}</p>
                        <p style="margin: 6px 0;"><strong>Contraseña temporal:</strong> {data['contraseña']}</p>
                    </div>
                    <h4 style="color: #39A900;">Paso a paso obligatorio</h4>
                    <ol>
                        <li>Ingresa a la plataforma usando la URL enviada en este correo.</li>
                        <li>Inicia sesión con tu usuario y contraseña temporal.</li>
                        <li>Cambia la contraseña temporal apenas ingreses y asigna una nueva contraseña personal y segura.</li>
                        <li>Completa tu perfil con toda tu información personal.</li>
                        <li>Carga una fotografía clara y actual de ti mismo. No deben aparecer otras personas, logos, objetos, paisajes ni imágenes que no correspondan a tu identidad.</li>
                        <li>Si vas a ingresar algún computador u otro equipo tecnológico, debes registrarlo en la plataforma antes de presentarte en portería.</li>
                    </ol>
                    <div style="background-color: #fff8f8; border-left: 4px solid #e74c3c; padding: 14px; margin-top: 22px; color: #555555;">
                        <strong>Importante:</strong> Si tu perfil no tiene una foto válida de ti, o si la imagen cargada no corresponde a tu identidad, no podrás ingresar a la institución hasta que la fotografía sea corregida y verificada.
                    </div>
                    <div style="background-color: #f9f9f9; border-left: 4px solid #39A900; padding: 12px; margin-top: 22px; font-size: 13px; color: #555555;">
                        <strong>Política de privacidad:</strong> La información registrada será utilizada únicamente para procesos de identificación, control de acceso y seguridad institucional del SENA Vélez, conforme a las políticas institucionales de protección de datos personales.
                    </div>
                </div>
                <div style="background-color: #f4f4f4; padding: 16px; text-align: center; font-size: 12px; color: #777777;">
                    <p style="margin: 0;">Este es un correo generado automáticamente por el Sistema de Acceso SENA Vélez. Por favor, no respondas a este mensaje.</p>
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
        if 'correo' in data:
            nuevo_correo = data['correo'].strip().lower()
            existente = Usuario.query.filter(Usuario.correo == nuevo_correo, Usuario.id != id).first()
            if existente:
                return jsonify({"status": "error", "message": "El correo ya está registrado"}), 400
            usuario.correo = nuevo_correo
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

@bp.route('/api/admin/importar_usuarios_excel', methods=['POST'])
@login_required
def api_importar_usuarios_excel():
    if not check_admin():
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No se subió ningún archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Archivo sin nombre"}), 400

    try:
        # Leer el excel
        df = pd.read_excel(file)
        
        # Validar columnas necesarias (mínimo Nombre y Correo)
        required_cols = ['Nombre', 'Correo']
        for col in required_cols:
            if col not in df.columns:
                return jsonify({"status": "error", "message": f"Falta la columna '{col}' en el Excel"}), 400

        # Obtener roles para mapeo
        roles_map = {r.nombre.lower(): r.id for r in Rol.query.all()}
        rol_usuario_id = roles_map.get('usuario')

        usuarios_creados = 0
        usuarios_omitidos = 0
        errores = []

        for index, row in df.iterrows():
            nombre = str(row.get('Nombre', '')).strip()
            correo = str(row.get('Correo', '')).strip().lower()
            documento = str(row.get('Documento', '')).strip() if pd.notnull(row.get('Documento')) else None
            cargo = str(row.get('Cargo', '')).strip() if pd.notnull(row.get('Cargo')) else 'Aprendiz'
            rol_nombre = str(row.get('Rol', '')).strip().lower() if pd.notnull(row.get('Rol')) else 'usuario'
            ficha = str(row.get('Ficha', '')).strip() if pd.notnull(row.get('Ficha')) else None
            programa = str(row.get('Programa', '')).strip() if pd.notnull(row.get('Programa')) else None
            horario = str(row.get('Horario', '')).strip() if pd.notnull(row.get('Horario')) else None
            password = str(row.get('Contraseña', 'Sena2024*')).strip()

            if not nombre or not correo:
                usuarios_omitidos += 1
                continue

            # Verificar si ya existe
            if Usuario.query.filter_by(correo=correo).first():
                usuarios_omitidos += 1
                continue

            rol_id = roles_map.get(rol_nombre, rol_usuario_id)
            if not rol_id:
                rol_id = rol_usuario_id

            try:
                nuevo_usuario = Usuario(
                    nombre=nombre,
                    correo=correo,
                    documento=documento,
                    rol_id=rol_id,
                    cargo=cargo,
                    ficha=ficha,
                    programa=programa,
                    horario=horario,
                    perfil_completo=False,
                    correo_verificado=True, # Por ser masivo, asumimos verificados o requerimos que completen perfil
                    debe_cambiar_contrasena=True
                )
                nuevo_usuario.set_password(password)
                db.session.add(nuevo_usuario)
                db.session.flush() # Para obtener ID si es necesario

                # --- ENVIAR CORREO DE BIENVENIDA ---
                from app.utils.email import enviar_correo
                asunto = "Bienvenido al Sistema de Acceso - SENA Vélez"
                link_login = url_for('auth.login', _external=True)
                cuerpo_html = f"""
                <div style="font-family: Arial, sans-serif; color: #333333; max-width: 680px; margin: 0 auto; border: 1px solid #dddddd; border-radius: 10px; overflow: hidden; background-color: #ffffff;">
                    <div style="background-color: #ffffff; padding: 24px 24px 16px 24px; text-align: center; border-bottom: 5px solid #39A900;">
                        <div style="font-size: 44px; font-weight: 900; color: #39A900; letter-spacing: 1px; line-height: 1;">SENA</div>
                        <h2 style="color: #39A900; margin: 12px 0 4px 0;">SENA Vélez Santander</h2>
                        <p style="color: #555555; margin: 0;">Sistema de Acceso y Carnet Digital</p>
                    </div>
                    <div style="padding: 26px;">
                        <h3>Hola, {nombre}</h3>
                        <p>Somos del <strong>SENA Vélez</strong> y te comunicamos que, para el ingreso a nuestra institución por portería, debes contar con un <strong>carnet digital activo</strong>.</p>
                        <p>Para iniciar el proceso, ingresa a la plataforma desde el siguiente enlace:</p>
                        <p style="text-align: center; margin: 26px 0;">
                            <a href="{link_login}" style="background-color: #39A900; color: #ffffff; padding: 13px 24px; text-decoration: none; border-radius: 7px; font-weight: bold; display: inline-block;">Ingresar a la plataforma</a>
                        </p>
                        <p>Si el botón no funciona, copia y pega esta URL en tu navegador:</p>
                        <p style="word-break: break-all;"><a href="{link_login}" style="color: #39A900;">{link_login}</a></p>
                        <p>Estas son tus credenciales de acceso temporal:</p>
                        <div style="background-color: #f5f5f5; padding: 16px; border-radius: 7px; margin-bottom: 22px; border-left: 4px solid #39A900;">
                            <p style="margin: 6px 0;"><strong>Usuario:</strong> {correo}</p>
                            <p style="margin: 6px 0;"><strong>Contraseña temporal:</strong> {password}</p>
                        </div>
                        <h4 style="color: #39A900;">Paso a paso obligatorio</h4>
                        <ol>
                            <li>Ingresa a la plataforma usando la URL enviada en este correo.</li>
                            <li>Inicia sesión con tu usuario y contraseña temporal.</li>
                            <li>Cambia la contraseña temporal apenas ingreses y asigna una nueva contraseña personal y segura.</li>
                            <li>Completa tu perfil con toda tu información personal.</li>
                            <li>Carga una fotografía clara y actual de ti mismo. No deben aparecer otras personas, logos, objetos, paisajes ni imágenes que no correspondan a tu identidad.</li>
                            <li>Si vas a ingresar algún computador u otro equipo tecnológico, debes registrarlo en la plataforma antes de presentarte en portería.</li>
                        </ol>
                        <div style="background-color: #fff8f8; border-left: 4px solid #e74c3c; padding: 14px; margin-top: 22px; color: #555555;">
                            <strong>Importante:</strong> Si tu perfil no tiene una foto válida de ti, o si la imagen cargada no corresponde a tu identidad, no podrás ingresar a la institución hasta que la fotografía sea corregida y verificada.
                        </div>
                        <div style="background-color: #f9f9f9; border-left: 4px solid #39A900; padding: 12px; margin-top: 22px; font-size: 13px; color: #555555;">
                            <strong>Política de privacidad:</strong> La información registrada será utilizada únicamente para procesos de identificación, control de acceso y seguridad institucional del SENA Vélez, conforme a las políticas institucionales de protección de datos personales.
                        </div>
                    </div>
                    <div style="background-color: #f4f4f4; padding: 16px; text-align: center; font-size: 12px; color: #777777;">
                        <p style="margin: 0;">Este es un correo generado automáticamente por el Sistema de Acceso SENA Vélez. Por favor, no respondas a este mensaje.</p>
                    </div>
                </div>
                """
                enviar_correo(correo, asunto, cuerpo_html)
                
                usuarios_creados += 1
            except Exception as e:
                errores.append(f"Fila {index+2}: {str(e)}")

        db.session.commit()
        
        msg = f"Importación finalizada. Creados: {usuarios_creados}, Omitidos: {usuarios_omitidos}."
        if errores:
            msg += f" Errores: {len(errores)}"

        return jsonify({
            "status": "success", 
            "message": msg,
            "detalles": {
                "creados": usuarios_creados,
                "omitidos": usuarios_omitidos,
                "errores": errores
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error al procesar Excel: {str(e)}"}), 500
