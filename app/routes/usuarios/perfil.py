from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ...models.usuarios import Usuario
from ...models.entidades import Equipo
from ...models.fichas import Ficha
from ...utils.barras import codigo128_svg, DatoNoCodificable
from ... import db
import os
import re
import shutil
import tempfile
from ...utils import get_colombia_time
from app.models.usuarios import TurnoCelador
from ...utils.security import sanitize_html
from ...models.usuarios import ESTADO_PENDIENTE, ESTADO_APROBADA
from ...utils.documentos import (TIPOS_DOCUMENTO, descripcion_formato,
                                 validar_documento)
from ...utils.imagenes import (
    extension_permitida,
    nombre_foto,
    procesar_foto,
    tiene_un_solo_rostro,
)
from . import bp
import logging

logger = logging.getLogger(__name__)

@bp.app_context_processor
def inyectar_tipos_documento():
    """Los tipos de documento y su formato, para pintarlos en los formularios."""
    return {
        'tipos_documento': TIPOS_DOCUMENTO,
        'formatos_documento': {c: descripcion_formato(c) for c in TIPOS_DOCUMENTO},
    }


def generar_barras(dato):
    """Codigo de barras Code128 del carnet, como SVG en linea.

    Sustituye al QR anterior porque el formato institucional impreso del SENA
    lleva codigo de barras. Va en SVG y sin ancho fijo para que el CSS lo
    estire al ancho del carnet: un codigo lineal leido desde la pantalla de un
    movil necesita todo el ancho que se le pueda dar.
    """
    if not dato:
        return None
    try:
        return codigo128_svg(str(dato), alto=70, mostrar_texto=False)
    except DatoNoCodificable:
        # Un documento con caracteres raros no debe tumbar el perfil entero:
        # se queda sin codigo y la persona ve el aviso de carnet bloqueado.
        logger.warning("No se pudo generar el codigo de barras del carnet.")
        return None


@bp.route('/profile')
@login_required
def profile():
    barcode_svg = None
    if current_user.perfil_completo and current_user.documento:
        barcode_svg = generar_barras(current_user.documento)

    equipos = Equipo.query.filter_by(usuario_id=current_user.id).all()

    turnos_hoy = []
    if current_user.puede_operar_porteria:
        turnos_hoy = TurnoCelador.query.filter(db.func.date(TurnoCelador.fecha_ingreso) == get_colombia_time().date()).all()

    # Solo las fichas activas, mas la del propio usuario aunque este archivada:
    # si no, al guardar el perfil perderia su ficha sin darse cuenta.
    fichas = Ficha.query.filter(
        db.or_(Ficha.activa.is_(True), Ficha.id == current_user.ficha_id)
    ).order_by(Ficha.numero).all()

    return render_template('usuarios/profile.html',
                           barcode_svg=barcode_svg, equipos=equipos,
                           turnos=turnos_hoy, fichas=fichas)

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
        #
        # El temporal va FUERA de static/: ahi quedaba descargable sin sesion en
        # una URL predecible mientras se procesaba (Werkzeug si sirve los
        # archivos que empiezan por punto), y si el proceso moria a mitad se
        # quedaba ahi para siempre sin que nada lo limpiara.
        carpeta_temporal = tempfile.mkdtemp(prefix='foto_perfil_')
        temporal = os.path.join(carpeta_temporal, nombre_final)

        # procesar_foto reescala, aplana transparencias, quita los metadatos
        # EXIF (que en fotos de celular llevan coordenadas GPS) y guarda un
        # JPEG optimizado. Tambien hace de validacion: un archivo que no sea
        # una imagen real falla aqui y nunca llega al disco definitivo.
        try:
            if not procesar_foto(archivo, temporal):
                return _error('No se pudo procesar la imagen. Intenta con un JPG o PNG.')

            valida, mensaje = tiene_un_solo_rostro(temporal)
            if not valida:
                return _error(mensaje)

            # os.replace es atomico: no queda una foto a medio escribir si algo
            # falla a mitad de la copia.
            os.makedirs(carpeta, exist_ok=True)
            os.replace(temporal, destino)
        finally:
            # Se borra la carpeta temporal siempre, incluso si algo revento.
            shutil.rmtree(carpeta_temporal, ignore_errors=True)

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
        # La comprobacion automatica confirma que la foto es utilizable, pero no
        # que la persona de la foto sea quien dice ser. Eso lo aprueba un
        # administrador: hasta entonces el carnet digital no se activa.
        current_user.foto_estado = ESTADO_PENDIENTE
        current_user.foto_motivo = None
        current_user.foto_revisada_por = None
        current_user.foto_fecha_revision = None
        current_user.foto_fecha_subida = get_colombia_time()

    # Nombres y apellidos por separado, tal como los pide el carnet oficial.
    # Son opcionales: quien no los llene sigue viendo su `nombre` repartido en
    # dos líneas, que es una aproximación, no un dato guardado.
    _SOLO_LETRAS = re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\'-]+$')
    for campo in ('nombres', 'apellidos'):
        valor = request.form.get(campo)
        if valor is None:
            continue
        valor = sanitize_html(valor).strip()
        if not valor:
            setattr(current_user, campo, None)
            continue
        if len(valor) > 100 or not _SOLO_LETRAS.match(valor):
            return _error('Nombres y apellidos solo admiten letras, espacios, '
                          'apóstrofos y guiones (máximo 100 caracteres).')
        setattr(current_user, campo, valor)

    documento_val = request.form.get('documento')
    tipo_val = request.form.get('tipo_documento') or current_user.tipo_documento or 'CC'
    if documento_val:
        # Se valida contra el tipo: sin esto, un dígito de más o de menos pasa
        # y después no se puede identificar a la persona en portería.
        limpio, error_doc = validar_documento(tipo_val, sanitize_html(documento_val))
        if error_doc:
            return _error(error_doc)
        existente = Usuario.query.filter(Usuario.documento == limpio,
                                         Usuario.id != current_user.id).first()
        if existente:
            return _error('Ese número de documento ya está registrado por otra persona.')
        current_user.tipo_documento = tipo_val.upper()
        current_user.documento = limpio
        
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
        
    # El aprendiz elige su ficha de una lista; el programa y la fecha de
    # finalización los hereda de ella y NO los teclea. Así dos aprendices de
    # la misma ficha no pueden acabar con datos distintos en el carnet.
    ficha_id_val = request.form.get('ficha_id')
    if ficha_id_val is not None and current_user.es_aprendiz_cargo:
        if ficha_id_val.strip():
            try:
                ficha = db.session.get(Ficha, int(ficha_id_val))
            except (TypeError, ValueError):
                ficha = None
            if not ficha:
                return _error('La ficha seleccionada no existe.')
            current_user.ficha_id = ficha.id
            # Se copia el número a la columna de texto histórica para que los
            # reportes y filtros que ya la usan sigan funcionando.
            current_user.ficha = ficha.numero
            current_user.programa = ficha.programa
        else:
            current_user.ficha_id = None


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
        # La ficha basta: de ella cuelgan el programa y la fecha. Se acepta
        # también la ficha en texto de quien ya la tenía antes de que
        # existiera la tabla, para no invalidarle un carnet que ya funcionaba.
        req_fields.append(current_user.ficha_id or current_user.ficha)

    # Check if profile is now complete
    # Los nombres antiguos siguen listados porque pueden persistir en la
    # columna `foto` de una base creada antes de los avatares por cargo.
    FOTOS_MARCADOR = (None, 'default-profile.png', 'default_profile.png')
    tiene_foto = current_user.foto not in FOTOS_MARCADOR
    # El carnet solo se activa con la foto ya aprobada: es lo que le da valor
    # a la verificacion en porteria.
    if all(req_fields) and tiene_foto and current_user.foto_estado == ESTADO_APROBADA:
        current_user.perfil_completo = True
        flash('¡Perfil completado! Tu carnet digital ya está disponible.', 'success')
    else:
        current_user.perfil_completo = False
        if tiene_foto and current_user.foto_estado == ESTADO_PENDIENTE:
            flash('Perfil actualizado. Tu foto quedó en revisión: cuando un '
                  'administrador la apruebe se activará tu carnet digital.',
                  'info')
        else:
            flash('Perfil actualizado. Completa todos los campos requeridos '
                  'para activar tu carnet.', 'warning')

    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": "Perfil actualizado correctamente.", "reload": True}
        
    return redirect(url_for('usuarios.profile'))
