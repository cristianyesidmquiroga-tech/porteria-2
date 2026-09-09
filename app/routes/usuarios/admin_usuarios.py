from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from ...models.usuarios import Usuario, Rol, TurnoCelador
from ...models.fichas import Ficha
from ... import db
from . import bp
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
import pandas as pd
import io
import secrets

from app.models.usuarios import CARGOS_VALIDOS, ROLES_IMPORTABLES
from app.utils.documentos import (TIPO_POR_DEFECTO, normalizar_numero,
                                  tipo_probable, validar_documento)
from app.utils.perfiles import perfil_esta_completo


def normalizar_documento(numero, tipo=None):
    """Valida y normaliza un documento igual que lo hace el perfil.

    Devuelve (tipo, numero_limpio, error). El panel de administración guardaba
    el texto crudo: con puntos, con letras o con la longitud que fuera. En
    portería el documento SÍ se valida y se busca normalizado, así que un
    documento guardado a mano dejaba a la persona sin poder entrar.

    Si no se indica el tipo se deduce del propio número, para no obligar al
    formulario del panel a mandarlo siempre. La deducción solo se acepta
    cuando el número es todo dígitos: para un número con letras el único tipo
    posible sería el pasaporte, que admite casi cualquier cosa, y adivinarlo
    convertiría un documento mal escrito en un pasaporte válido.
    """
    numero = (numero or '').strip()
    if not numero:
        return (tipo or '').strip().upper() or None, None, None
    tipo = (tipo or '').strip().upper()
    if not tipo:
        if not normalizar_numero(numero).isdigit():
            return None, None, ('Indica el tipo de documento: un número con '
                                'letras solo es válido como pasaporte y hay '
                                'que declararlo.')
        tipo = tipo_probable(numero)
    limpio, error = validar_documento(tipo, numero)
    if error:
        return tipo, None, error
    return tipo, limpio, None


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
    
    return render_template('usuarios/gestion.html', usuarios=usuarios, roles=roles,
                           cargos_validos=CARGOS_VALIDOS)

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

@bp.route('/api/admin/correos_fallidos')
@login_required
def api_correos_fallidos():
    """Ultimos fallos de entrega de correo que ya se dieron por perdidos.

    enviar_correo() devuelve True en cuanto encola el mensaje, no cuando el
    servidor SMTP confirma la entrega: la peticion web no puede esperar a
    eso. El resultado real (entregado, reintentado o descartado) quedaba solo
    en el log del hilo enviador, que nadie revisa. Esta ruta le da al
    administrador una forma de ver, sin entrar al servidor, a quien no le
    llego un correo y por que.
    """
    if not check_admin():
        return jsonify({"status": "error", "message": "No autorizado"}), 403
    from app.utils.email import fallos_recientes
    return jsonify({"status": "success", "fallos": fallos_recientes()})


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

        # El documento se valida y se normaliza igual que en el perfil y en el
        # registro: es la clave con la que se identifica a la persona en
        # portería y tiene que quedar guardada siempre de la misma forma.
        tipo_documento, documento, error_documento = normalizar_documento(
            data.get('documento'), data.get('tipo_documento'))
        if error_documento:
            return jsonify({"status": "error", "message": error_documento}), 400

        # Verificar existencia
        if Usuario.query.filter_by(correo=data['correo']).first():
            return jsonify({"status": "error", "message": "El correo ya está registrado"}), 400
        if documento and Usuario.query.filter_by(documento=documento).first():
            return jsonify({"status": "error", "message": "El documento ya está registrado"}), 400

        from app.utils.email import enviar_correo
        from app.models.usuarios import Rol
        
        rol = Rol.query.get(int(data['rol_id']))
        es_usuario_normal = rol and rol.nombre == 'Usuario'
        cargo = data.get('cargo') or None
        if cargo and cargo not in CARGOS_VALIDOS:
            return jsonify({"status": "error",
                            "message": "El cargo seleccionado no es válido"}), 400

        nuevo_usuario = Usuario(
            nombre=data['nombre'],
            correo=data['correo'].lower(),
            documento=documento,
            tipo_documento=tipo_documento or TIPO_POR_DEFECTO,
            rol_id=int(data['rol_id']),
            cargo=cargo,
            ficha=data.get('ficha'),
            programa=data.get('programa'),
            horario=data.get('horario'),
            perfil_completo=False if es_usuario_normal else True,
            correo_verificado=True,
            debe_cambiar_contrasena=es_usuario_normal
        )
        nuevo_usuario.set_password(data['contraseña'])
        # Si esa ficha ya esta registrada, el aprendiz hereda de una vez su
        # programa y su fecha de finalizacion en lugar de quedarse con el
        # numero suelto.
        Ficha.enlazar_por_numero(nuevo_usuario, data.get('ficha'))

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



        from app.models.accesos import Auditoria
        db.session.add(Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='usuarios',
            registro_id=nuevo_usuario.id,
            accion='Creacion de Usuario',
            autorizado_por=data.get('autorizado_por'),
            motivo=data.get('motivo'),
            detalles=(f"Alta de {nuevo_usuario.correo} con rol_id={nuevo_usuario.rol_id} "
                      f"y cargo={nuevo_usuario.cargo}"),
        ))
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
        cargo_anterior = usuario.cargo
        # Actualizar datos básicos
        if 'nombre' in data: usuario.nombre = data['nombre']
        if 'correo' in data:
            nuevo_correo = data['correo'].strip().lower()
            existente = Usuario.query.filter(Usuario.correo == nuevo_correo, Usuario.id != id).first()
            if existente:
                return jsonify({"status": "error", "message": "El correo ya está registrado"}), 400
            usuario.correo = nuevo_correo
        if 'documento' in data or 'tipo_documento' in data:
            # El tipo y el número van juntos: si solo se cambiaba uno, el tipo
            # podía acabar diciendo "tarjeta de identidad" sobre un número de
            # cédula, y el carnet imprime la abreviatura del tipo.
            tipo_pedido = data.get('tipo_documento') or (
                usuario.tipo_documento if 'documento' not in data else None)
            numero_pedido = data['documento'] if 'documento' in data else usuario.documento
            tipo_documento, nuevo_documento, error_documento = normalizar_documento(
                numero_pedido, tipo_pedido)
            if error_documento:
                return jsonify({"status": "error", "message": error_documento}), 400
            if nuevo_documento:
                # La columna es unica: sin esta comprobacion el choque salia
                # como IntegrityError y se devolvia un 500 con el texto crudo
                # de la excepcion al cliente.
                duplicado = Usuario.query.filter(
                    Usuario.documento == nuevo_documento, Usuario.id != id).first()
                if duplicado:
                    return jsonify({"status": "error",
                                    "message": "El documento ya esta registrado"}), 400
            usuario.documento = nuevo_documento
            if tipo_documento:
                usuario.tipo_documento = tipo_documento
        if 'cargo' in data:
            cargo = data.get('cargo') or None
            if cargo and cargo not in CARGOS_VALIDOS:
                return jsonify({"status": "error",
                                "message": "El cargo seleccionado no es válido"}), 400
            usuario.cargo = cargo
        if 'rol_id' in data: usuario.rol_id = int(data['rol_id'])
        if 'ficha' in data:
            usuario.ficha = data['ficha']
            Ficha.enlazar_por_numero(usuario, data['ficha'])
        if 'programa' in data: usuario.programa = data['programa']
        if 'horario' in data: usuario.horario = data['horario']
        
        if 'verificado' in data: 
            usuario.correo_verificado = data['verificado']
            
        if 'estado_bloqueo' in data:
            if data['estado_bloqueo'] == 'desbloquear':
                usuario.bloqueado_hasta = None
                usuario.intentos_fallidos = 0
            
        if 'rol_id' in data or ('contraseña' in data and data['contraseña'].strip()):
            # Cambiar el rol o la contrasena debe expulsar las sesiones activas:
            # si no, un intruso conserva el acceso pese al restablecimiento.
            usuario.session_token = None

        if 'contraseña' in data and data['contraseña'].strip():
            usuario.set_password(data['contraseña'])

        # El perfil del carnet se deriva del cargo: a un aprendiz se le exige
        # ficha y a los demás no. Cambiar el cargo sin recalcular dejaba la
        # marca en verdadero y se emitía un carnet de aprendiz con la ficha y
        # la fecha de finalización vacías. Se usa la MISMA regla que aplica la
        # persona al guardar su perfil (app/utils/perfiles.py).
        if usuario.cargo != cargo_anterior:
            rol_actual = db.session.get(Rol, usuario.rol_id)
            # Solo se recalcula a quien de verdad debe completar su perfil.
            # Las cuentas de gestión se crean con la marca puesta a mano y no
            # tienen foto ni tipo de sangre: recalcularlas las dejaría sin
            # poder entrar al sistema.
            if rol_actual and rol_actual.nombre == 'Usuario':
                usuario.perfil_completo = perfil_esta_completo(usuario)

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
        # Todas las columnas se leen como TEXTO. Sin dtype=str, una columna de
        # documentos con alguna celda vacía la deduce pandas como decimal y el
        # documento llega como '1098765432.0', que es lo que se guardaba en la
        # base: en portería la persona teclea su documento real, no coincide
        # con ninguno, y se queda fuera. Lo mismo valía para fichas y horarios.
        df = pd.read_excel(file, dtype=str)
        
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
        # Documentos ya usados en este mismo archivo: la columna es única y un
        # choque saltaría como IntegrityError al vaciar la sesión, tumbando
        # también las filas que iban bien.
        documentos_del_lote = set()

        def _texto(row, columna):
            """Celda como texto limpio, o None si viene vacía."""
            valor = row.get(columna)
            if valor is None or pd.isnull(valor):
                return None
            texto = str(valor).strip()
            return texto or None

        for index, row in df.iterrows():
            nombre = _texto(row, 'Nombre') or ''
            correo = (_texto(row, 'Correo') or '').lower()

            # Las filas que no se van a crear se descartan antes de mirar el
            # resto: si no, una fila vacía del final del Excel generaba avisos
            # de documento y de cargo sobre alguien que nunca se importa.
            if not nombre or not correo:
                usuarios_omitidos += 1
                continue
            # Un correo repetido se omite, no tumba el lote: la columna es
            # única y el choque saltaría al vaciar la sesión.
            if Usuario.query.filter_by(correo=correo).first():
                usuarios_omitidos += 1
                continue

            # El documento pasa por la misma validación que el perfil y la
            # portería. Si no la pasa, la persona se importa SIN documento y
            # queda el aviso: guardar un documento inválido es peor, porque
            # después no coincide con el que teclea en portería.
            tipo_documento, documento, error_documento = normalizar_documento(
                _texto(row, 'Documento'), _texto(row, 'Tipo Documento'))
            if error_documento:
                errores.append(f"Fila {index + 2}: documento no valido "
                               f"({error_documento}) Se importo sin documento.")
                documento = None
            if documento and (documento in documentos_del_lote
                              or Usuario.query.filter_by(documento=documento).first()):
                errores.append(f"Fila {index + 2}: el documento ya esta "
                               f"registrado. Se importo sin documento.")
                documento = None
            # El cargo gobierna permisos (porteria, asesoria, asistencia) y el
            # rol da acceso total. Tomarlos tal cual del Excel significa que quien
            # PREPARA la hoja decide quien es administrador, sin que el admin que
            # la sube se entere. Ambos pasan por lista blanca.
            cargo_hoja = _texto(row, 'Cargo') or ''
            cargo = cargo_hoja if cargo_hoja in CARGOS_VALIDOS else 'Aprendiz'
            if cargo_hoja and cargo_hoja not in CARGOS_VALIDOS:
                errores.append(f"Fila {index + 2}: cargo '{cargo_hoja}' no valido, "
                               f"se asigno Aprendiz.")

            rol_hoja = (_texto(row, 'Rol') or '').lower()
            # 'Admin' NUNCA se concede desde una importacion masiva.
            rol_nombre = rol_hoja if rol_hoja in ROLES_IMPORTABLES else 'usuario'
            if rol_hoja and rol_hoja not in ROLES_IMPORTABLES:
                errores.append(f"Fila {index + 2}: rol '{rol_hoja}' no permitido en "
                               f"importacion, se asigno Usuario.")
            ficha = _texto(row, 'Ficha')
            programa = _texto(row, 'Programa')
            horario = _texto(row, 'Horario')
            # Una contrasena por defecto escrita en el codigo permite entrar a
            # cualquier cuenta importada antes de que su dueno la use por primera
            # vez. Cada fila recibe una temporal aleatoria distinta.
            password = _texto(row, 'Contraseña') or secrets.token_urlsafe(12)

            rol_id = roles_map.get(rol_nombre, rol_usuario_id)
            if not rol_id:
                rol_id = rol_usuario_id

            try:
                nuevo_usuario = Usuario(
                    nombre=nombre,
                    correo=correo,
                    documento=documento,
                    tipo_documento=tipo_documento or TIPO_POR_DEFECTO,
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
                Ficha.enlazar_por_numero(nuevo_usuario, ficha)
                db.session.add(nuevo_usuario)
                db.session.flush() # Para obtener ID si es necesario
                if documento:
                    documentos_del_lote.add(documento)
                usuarios_creados += 1
            except Exception as e:
                # La fila que falla se anota y el lote sigue: una sola fila
                # corrupta no puede dejar sin importar a las demás.
                errores.append(f"Fila {index+2}: {str(e)}")
                continue

            try:
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
            except Exception as e:
                # El usuario YA está creado: que falle el correo de bienvenida
                # no debe descontarlo del lote ni interrumpir la importación.
                errores.append(f"Fila {index+2}: usuario creado, pero no se "
                               f"pudo enviar el correo de bienvenida ({e}).")

        # El alta individual sí se auditaba; la masiva no dejaba ningún rastro,
        # justo donde se asignan roles y cargos a mucha gente de una vez.
        from app.models.accesos import Auditoria
        db.session.add(Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='usuarios',
            registro_id=0,
            accion='Importación masiva de usuarios',
            autorizado_por=current_user.nombre,
            motivo='Carga de usuarios desde archivo Excel',
            detalles=(f"Archivo: {file.filename}. Creados: {usuarios_creados}, "
                      f"omitidos: {usuarios_omitidos}, avisos: {len(errores)}."),
        ))
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
