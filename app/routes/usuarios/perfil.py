from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ...models.usuarios import Usuario
from ...models.entidades import Equipo
from ... import db
import qrcode
import io
import base64
import os
import re
from ...utils import get_colombia_time
from app.models.usuarios import TurnoCelador
from ...utils.security import sanitize_html
from ...utils.imagenes import (
    extension_permitida,
    nombre_foto,
    procesar_foto,
    tiene_un_solo_rostro,
)
from . import bp
import logging

logger = logging.getLogger(__name__)

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@bp.route('/profile')
@login_required
def profile():
    qr_code = None
    if current_user.perfil_completo and current_user.documento:
        qr_code = generate_qr(current_user.documento)

    equipos = Equipo.query.filter_by(usuario_id=current_user.id).all()
    
    turnos_hoy = []
    if current_user.puede_operar_porteria:
        turnos_hoy = TurnoCelador.query.filter(db.func.date(TurnoCelador.fecha_ingreso) == get_colombia_time().date()).all()

    return render_template('usuarios/profile.html',
                           qr_code=qr_code, equipos=equipos, turnos=turnos_hoy)

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def _error(mensaje):
        if es_ajax:
            return {"status": "error", "message": mensaje}, 400
        flash(mensaje, 'danger')
        return redirect(url_for('usuarios.profile'))

    archivo = request.files.get('foto')
    if archivo and archivo.filename:
        if not extension_permitida(archivo.filename):
            return _error('Solo se permiten imágenes (png, jpg, jpeg, webp, bmp, tiff).')

        carpeta = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
        nombre_final = nombre_foto(current_user.id)
        destino = os.path.join(carpeta, nombre_final)

        # Se escribe primero a un temporal: si la imagen no es valida o no pasa
        # la validacion facial, la foto anterior del usuario sigue intacta.
        temporal = os.path.join(carpeta, f".tmp_{nombre_final}")

        # procesar_foto reescala, aplana transparencias, quita los metadatos
        # EXIF (que en fotos de celular llevan coordenadas GPS) y guarda un
        # JPEG optimizado. Tambien hace de validacion: un archivo que no sea
        # una imagen real falla aqui y nunca llega al disco definitivo.
        if not procesar_foto(archivo, temporal):
            if os.path.exists(temporal):
                os.remove(temporal)
            return _error('No se pudo procesar la imagen. Intenta con un JPG o PNG.')

        valida, mensaje = tiene_un_solo_rostro(temporal)
        if not valida:
            os.remove(temporal)
            return _error(mensaje)

        # os.replace es atomico: no queda una foto a medio escribir si algo falla.
        os.replace(temporal, destino)

        # Las fotos anteriores tenian el nombre original del archivo, asi que
        # cada cambio de foto dejaba la vieja huerfana en el disco para siempre.
        anterior = current_user.foto
        if anterior and anterior != nombre_final:
            ruta_anterior = os.path.join(carpeta, anterior)
            if os.path.isfile(ruta_anterior):
                try:
                    os.remove(ruta_anterior)
                except OSError:
                    logger.warning("No se pudo borrar la foto anterior %s", anterior)

        current_user.foto = nombre_final

    documento_val = request.form.get('documento')
    if documento_val:
        current_user.documento = sanitize_html(documento_val).strip()
        
    programa_val = request.form.get('programa')
    if programa_val:
        # Limpieza suave: solo letras, espacios, acentos y Ñ
        programa_clean = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', programa_val).strip()
        
        # Si había contenido pero tras la limpieza quedó diferente (tenía números)
        if programa_val.strip() and programa_clean != programa_val.strip():
            msg = "El campo 'Programa' o 'Área' solo permite letras y espacios. Por favor, retira números o símbolos."
            flash(msg, 'danger')
            return redirect(url_for('usuarios.profile'))
            
        current_user.programa = programa_clean.title()
        
    ficha_val = request.form.get('ficha')
    if ficha_val:
        current_user.ficha = sanitize_html(ficha_val).strip()
        
    sangre_val = request.form.get('tipo_sangre', '').strip().upper()
    valid_blood_types = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
    if sangre_val in valid_blood_types:
        current_user.tipo_sangre = sangre_val
    elif sangre_val:
        msg = 'Tipo de sangre no válido. Por favor selecciona de la lista.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"status": "error", "message": msg}, 400
        flash(msg, 'danger')
        return redirect(url_for('usuarios.profile'))

    # Construct required fields according to role
    req_fields = [
        current_user.documento,
        current_user.tipo_sangre,
        current_user.foto]
    if current_user.es_aprendiz_cargo:
        req_fields.extend([current_user.programa, current_user.ficha])

    # Check if profile is now complete
    if all(req_fields) and current_user.foto not in (None, 'default-profile.png', 'default_profile.png'):
        current_user.perfil_completo = True
        flash('¡Perfil completado! Tu carnet digital ya está disponible.', 'success')
    else:
        current_user.perfil_completo = False
        flash(
            'Perfil actualizado. Asegúrate de llenar todos los campos requeridos para ver tu carnet.',
            'warning')

    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": "Perfil actualizado correctamente.", "reload": True}
        
    return redirect(url_for('usuarios.profile'))
