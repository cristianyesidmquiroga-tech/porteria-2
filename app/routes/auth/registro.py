from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from ...models.usuarios import Usuario, Rol
from ... import db
import secrets
import string
import re
from datetime import datetime, timedelta
from ...utils.security import sanitize_html, validar_contrasena, correo_permitido
from ...utils import get_colombia_time
from flask import current_app
import logging

logger = logging.getLogger(__name__)
from ...utils.email import enviar_correo
from . import bp

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Eliminamos la restricción de admin para permitir registro público
    # if not current_user.es_admin:
    #     flash("Acceso denegado. Solo los administradores pueden crear nuevas cuentas.", "danger")
    #     return redirect(url_for('main.index'))

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 1. Datos Básicos
        nombre_raw = request.form.get('nombre')
        nombre = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', nombre_raw).strip().title() if nombre_raw else None
        
        correo = (sanitize_html(request.form.get('correo')) or '').lower().strip()
        documento_raw = (sanitize_html(request.form.get('documento')) or '').strip()
        documento = documento_raw if documento_raw else None
        contraseña = request.form.get('password')
        # 2. Selección de Cargo (Solo Admin elige, público es Aprendiz)
        if current_user.is_authenticated and current_user.es_admin:
            cargo = request.form.get('cargo')
        else:
            cargo = 'Aprendiz'
        
        if not cargo:
            cargo = 'Aprendiz'

        # 3. Asignación Automática de Rol 'Usuario'
        rol_usuario = Rol.query.filter_by(nombre='Usuario').first()
        if not rol_usuario:
            msg = "Error de Sistema: Rol base no encontrado."
            if is_ajax: return {"status": "error", "message": msg}, 500
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 4. Datos Dinámicos por Cargo
        ficha = ((sanitize_html(request.form.get('ficha')) or '').strip() or None) if cargo == 'Aprendiz' else None
        horario = request.form.get('horario') if cargo == 'Aprendiz' else None
        programa_raw = request.form.get('programa')
        programa = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s0-9]', '', programa_raw).strip() if programa_raw else None

        # 5a. Consentimiento de tratamiento de datos (Ley 1581 de 2012):
        # sin autorizacion expresa del titular no se puede crear la cuenta.
        if not request.form.get('acepta_datos'):
            msg = ('Debes autorizar el tratamiento de tus datos personales '
                   'para poder registrarte.')
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 5b. Datos minimos
        if not nombre or not correo:
            msg = 'El nombre y el correo son obligatorios.'
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 5c. Contrasena: antes no se validaba nada y se podia crear una
        # cuenta con contrasena vacia.
        error_contrasena = validar_contrasena(contraseña, request.form.get('confirm_password'))
        if error_contrasena:
            if is_ajax: return {"status": "error", "message": error_contrasena}, 400
            flash(error_contrasena, 'danger')
            return redirect(url_for('auth.register'))

        # 5d. Dominios permitidos (configurable con DOMINIOS_REGISTRO)
        dominios = current_app.config.get('DOMINIOS_REGISTRO') or []
        if not correo_permitido(correo, dominios):
            msg = ('Solo se permiten correos de los dominios institucionales: '
                   + ', '.join(dominios))
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 5e. Validaciones de existencia
        if Usuario.query.filter_by(correo=correo).first():
            # Mensaje neutro: confirmar que un correo o una cedula ya existen
            # permite enumerar las cuentas del centro desde un endpoint publico.
            msg = ('Si los datos son correctos, recibiras un correo con las '
                   'instrucciones para continuar.')
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))
            
        if documento and Usuario.query.filter_by(documento=documento).first():
            msg = ('Si los datos son correctos, recibiras un correo con las '
                   'instrucciones para continuar.')
            if is_ajax: return {"status": "error", "message": msg}, 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # 6. Lógica de Consistencia (Solo para Aprendices)
        if cargo == 'Aprendiz' and ficha:
            # Ahora buscamos consistencia por cargo, no por rol_id
            existing = Usuario.query.filter(Usuario.ficha == ficha, Usuario.cargo == 'Aprendiz').first()
            if existing and ((existing.programa or '').lower() != (programa or '').lower()
                             or existing.horario != horario):
                msg = "Consistencia de ficha fallida. Verifica Programa/Jornada para esta ficha."
                if is_ajax: return {"status": "error", "message": msg}, 400
                flash(msg, 'danger')
                return redirect(url_for('auth.register'))

        try:
            new_user = Usuario(
                nombre=nombre,
                documento=documento,
                correo=correo,
                rol_id=rol_usuario.id, # Siempre Rol Usuario
                ficha=ficha,
                programa=programa,
                horario=horario,
                cargo=cargo,
                correo_verificado=False)
            
            new_user.set_password(contraseña)
            new_user.codigo_verificacion = ''.join(secrets.choice(string.digits) for _ in range(6))
            new_user.codigo_expiracion = get_colombia_time() + timedelta(minutes=15)

            db.session.add(new_user)
            db.session.commit()

            asunto = "Código de verificación - Sistema de Acceso SENA"
            link_verificacion = url_for('auth.verificar_correo', _external=True)
            cuerpo_html = f"""
            <div style="font-family: Arial, sans-serif; color: #333; max-width: 640px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background-color: #ffffff;">
                <div style="background-color: #39A900; padding: 24px; text-align: center;">
                    <h2 style="color: white; margin: 0;">SENA - Regional Santander</h2>
                    <p style="color: white; margin: 6px 0 0 0;">Centro de Gestión Agroempresarial del Oriente - Vélez</p>
                </div>
                <div style="padding: 24px;">
                    <h3>Hola, {nombre}</h3>
                    <p>Tu cuenta fue creada correctamente en el Sistema de Acceso SENA. Para activar tu acceso, verifica tu correo usando el siguiente código:</p>
                    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 6px; text-align: center; margin: 22px 0;">
                        <span style="font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #39A900;">{new_user.codigo_verificacion}</span>
                    </div>
                    <p>Este código vence en 15 minutos.</p>
                    <p style="text-align: center; margin: 28px 0;">
                        <a href="{link_verificacion}" style="background-color: #39A900; color: #ffffff; padding: 12px 22px; text-decoration: none; border-radius: 6px; font-weight: bold;">Ir a verificar mi correo</a>
                    </p>
                    <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all;"><a href="{link_verificacion}" style="color: #39A900;">{link_verificacion}</a></p>
                    <div style="background-color: #f9f9f9; border-left: 4px solid #39A900; padding: 12px; margin-top: 24px; font-size: 13px; color: #555;">
                        <strong>Política de privacidad:</strong> La información enviada en este correo es de uso exclusivo del Sistema de Acceso SENA y será tratada conforme a las políticas institucionales de protección de datos personales. No compartas este código con terceros.
                    </div>
                </div>
                <div style="background-color: #f4f4f4; padding: 16px; text-align: center; font-size: 12px; color: #777;">
                    <p style="margin: 0;">Este es un correo generado automáticamente por el sistema. Por favor, no respondas a este mensaje.</p>
                </div>
            </div>
            """
            enviado = enviar_correo(correo, asunto, cuerpo_html)
            
            if not enviado:
                logger.warning("No se pudo enviar el correo de verificacion al usuario %s. "
                               "Revisa la configuracion SMTP.", new_user.id)

            

            msg = '¡Registro exitoso! Revisa tu correo.'
            if is_ajax: return {"status": "success", "message": msg, "redirect": url_for('auth.login')}
            flash(msg, 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logger.exception("Error durante el registro")
            if is_ajax: return {"status": "error", "message": "Error interno al procesar el registro."}, 500
            flash("Error interno durante el registro.", 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')
