from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ... import db
import random
import string
from datetime import datetime, timedelta
from ...utils.email import enviar_correo
from . import bp

@bp.route('/verificar', methods=['GET', 'POST'])
@login_required
def verificar_correo():
    if getattr(current_user, 'correo_verificado', False):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        if getattr(current_user, 'codigo_verificacion', '') == codigo:
            if current_user.codigo_expiracion and datetime.utcnow() > current_user.codigo_expiracion:
                flash('El código ha expirado. Por favor, solicita uno nuevo.', 'danger')
                return redirect(url_for('auth.verificar_correo'))

            current_user.correo_verificado = True
            current_user.codigo_verificacion = None
            current_user.codigo_expiracion = None
            db.session.commit()

            flash('¡Correo verificado exitosamente!', 'success')
            if not getattr(current_user, 'perfil_completo', True):
                return redirect(url_for('usuarios.profile'))
            return redirect(url_for('main.index'))
        else:
            flash('Código incorrecto. Intenta nuevamente.', 'danger')

    if current_user.codigo_verificacion:
        print(f"\n[ACCESO] Codigo para {current_user.correo}: {current_user.codigo_verificacion}", flush=True)
        # Registro en Archivo (Fail-safe)
        try:
            with open('CODIGOS_DESARROLLO.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Acceso: {current_user.correo} -> CODIGO: {current_user.codigo_verificacion}\n")
        except: pass

    return render_template('auth/verificar.html')

@bp.route('/reenviar_codigo', methods=['POST'])
@login_required
def reenviar_codigo():
    if not getattr(current_user, 'correo_verificado', False):
        current_user.codigo_verificacion = ''.join(random.choices(string.digits, k=6))
        current_user.codigo_expiracion = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

        asunto = "Nuevo código de verificación - Sistema de Acceso SENA"
        link_verificacion = url_for('auth.verificar_correo', _external=True)
        cuerpo_html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 640px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background-color: #ffffff;">
            <div style="background-color: #39A900; padding: 24px; text-align: center;">
                <h2 style="color: white; margin: 0;">SENA - Regional Santander</h2>
                <p style="color: white; margin: 6px 0 0 0;">Centro de Gestión Agroempresarial del Oriente - Vélez</p>
            </div>
            <div style="padding: 24px;">
                <h3>Hola, {current_user.nombre}</h3>
                <p>Solicitaste un nuevo código para verificar tu correo. Usa el siguiente código:</p>
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 6px; text-align: center; margin: 22px 0;">
                    <span style="font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #39A900;">{current_user.codigo_verificacion}</span>
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
        enviar_correo(current_user.correo, asunto, cuerpo_html)
        
        print("\n" + "=" * 50, flush=True)
        print(f"REENVIO DE CORREO A: {current_user.correo}", flush=True)
        print(f"NUEVO CODIGO DE VERIFICACION: {current_user.codigo_verificacion}", flush=True)
        print("=" * 50 + "\n", flush=True)

        # Registro en Archivo (Fail-safe)
        try:
            with open('CODIGOS_DESARROLLO.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Reenvio: {current_user.correo} -> CODIGO: {current_user.codigo_verificacion}\n")
        except: pass

        flash('Se ha reenviado un nuevo código a tu correo.', 'info')
    return redirect(url_for('auth.verificar_correo'))
