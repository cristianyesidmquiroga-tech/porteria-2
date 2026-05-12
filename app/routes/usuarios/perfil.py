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
from datetime import date
from werkzeug.utils import secure_filename
from app.models.usuarios import TurnoCelador
from . import bp

def sanitize_html(text):
    if not text: return text
    return re.sub(r'<[^>]*?>', '', str(text))

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
        turnos_hoy = TurnoCelador.query.filter(db.func.date(TurnoCelador.fecha_ingreso) == date.today()).all()

    return render_template('usuarios/profile.html',
                           qr_code=qr_code, equipos=equipos, turnos=turnos_hoy)

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if 'foto' in request.files:
        file = request.files['foto']
        if file.filename != '':
            ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff'}
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            if ext not in ALLOWED_EXTENSIONS:
                msg = 'Solo se permiten archivos de imagen (png, jpg, jpeg, webp, etc).'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return {"status": "error", "message": msg}, 400
                flash(msg, 'danger')
                return redirect(url_for('usuarios.profile'))
            
            filename = secure_filename(file.filename)
            unique_filename = f"user_{current_user.id}_{filename}"
            upload_path = os.path.join(
                current_app.root_path,
                'static',
                'uploads',
                'profiles',
                unique_filename)
            file.save(upload_path)
            
            # --- VALIDACIÓN FACIAL ---
            try:
                import cv2
                # Cargar el clasificador de rostros (Haar Cascade)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                
                # Leer la imagen guardada
                img = cv2.imread(upload_path)
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    if len(faces) == 0:
                        if os.path.exists(upload_path): os.remove(upload_path)
                        msg = "No se detectó ningún rostro en la foto. Por favor sube una foto real donde se vea tu cara."
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return {"status": "error", "message": msg}, 400
                        flash(msg, 'danger')
                        return redirect(url_for('usuarios.profile'))
                    
                    if len(faces) > 1:
                        if os.path.exists(upload_path): os.remove(upload_path)
                        msg = "Se detectó más de una persona en la foto. La foto de perfil debe ser individual."
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return {"status": "error", "message": msg}, 400
                        flash(msg, 'danger')
                        return redirect(url_for('usuarios.profile'))
                else:
                    # Si no se pudo leer la imagen (formato extraño), la borramos por seguridad
                    if os.path.exists(upload_path): os.remove(upload_path)
                    msg = "No se pudo procesar la imagen. Intenta con otro formato (JPG o PNG)."
                    flash(msg, 'danger')
                    return redirect(url_for('usuarios.profile'))
                    
            except Exception as e:
                print(f"Error en validación facial (omitido para no bloquear): {e}")
                # Si falla por algo técnico de la librería, dejamos pasar la foto para no bloquear el sistema
            
            current_user.foto = unique_filename

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
    if all(req_fields) and current_user.foto != 'default_profile.png':
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
