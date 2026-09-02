"""Cola de aprobación de fotos de perfil.

La comprobación automática (`app/utils/imagenes.py`) confirma que la foto es
utilizable: un solo rostro, nítida, con luz suficiente y que sea una fotografía
real y no un dibujo. Lo que ningún análisis de imagen puede confirmar es que la
persona de la foto sea quien dice ser.

Por eso un administrador revisa cada foto antes de que el carnet digital quede
activo. Hasta entonces el usuario no tiene código de barras y no puede entrar por portería con
el carnet, aunque su perfil esté completo en todo lo demás.

Toda decisión queda en `Auditoria`: quién revisó, cuándo y por qué.
"""
import logging
import os

from ...utils.fotos import carpeta_fotos
from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ... import db
from ...models.accesos import Auditoria
from ...models.mensajes import registrar_mensaje
from ...models.usuarios import (
    ESTADO_APROBADA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    ESTADO_SIN_FOTO,
    Usuario,
)
from ...utils import get_colombia_time
from ...utils.email import enviar_correo
from ...utils.security import sanitize_html
from . import bp

logger = logging.getLogger(__name__)

POR_PAGINA = 24


MOTIVOS_FRECUENTES = [
    'La foto no corresponde a la persona registrada.',
    'No se distingue el rostro con claridad.',
    'El rostro está tapado (gorra, capucha, mascarilla o bufanda).',
    'Aparece más de una persona en la foto.',
    'No es una fotografía real (dibujo, personaje o imagen de internet).',
    'La foto está muy oscura o a contraluz.',
]


def _solo_admin():
    if current_user.es_admin:
        return None
    flash('Acceso denegado. Área exclusiva para administradores.', 'danger')
    return redirect(url_for('main.index'))


def _avisar_por_correo(usuario, aprobada, motivo=None):
    """Avisa al usuario del resultado. Un fallo de correo no debe tumbar la
    revisión, así que se registra y se sigue."""
    enlace = url_for('usuarios.profile', _external=True)
    if aprobada:
        asunto = 'Tu foto fue aprobada - Sistema de Acceso SENA'
        cuerpo = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 620px; margin: 0 auto;">
            <div style="background-color: #39A900; padding: 20px; text-align: center;">
                <h2 style="color: #fff; margin: 0;">SENA - Sistema de Acceso</h2>
            </div>
            <div style="padding: 24px;">
                <h3>Hola, {usuario.nombre}</h3>
                <p>Tu foto de perfil fue <strong>aprobada</strong>. Tu carnet digital
                   ya está activo y puedes usarlo para ingresar por portería.</p>
                <p style="text-align:center; margin: 26px 0;">
                    <a href="{enlace}" style="background-color:#39A900; color:#fff; padding:12px 22px;
                       text-decoration:none; border-radius:6px; font-weight:bold;">Ver mi carnet</a>
                </p>
            </div>
        </div>
        """
    else:
        asunto = 'Debes corregir tu foto de perfil - Sistema de Acceso SENA'
        cuerpo = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 620px; margin: 0 auto;">
            <div style="background-color: #39A900; padding: 20px; text-align: center;">
                <h2 style="color: #fff; margin: 0;">SENA - Sistema de Acceso</h2>
            </div>
            <div style="padding: 24px;">
                <h3>Hola, {usuario.nombre}</h3>
                <p>Tu foto de perfil <strong>no fue aprobada</strong> y tu carnet digital
                   sigue inactivo. Motivo:</p>
                <div style="background-color:#fff8f8; border-left:4px solid #e74c3c;
                            padding:14px; margin:18px 0;">{motivo}</div>
                <p>Sube una foto nueva que cumpla los requisitos y vuelve a quedar en revisión.</p>
                <p style="text-align:center; margin: 26px 0;">
                    <a href="{enlace}" style="background-color:#39A900; color:#fff; padding:12px 22px;
                       text-decoration:none; border-radius:6px; font-weight:bold;">Subir otra foto</a>
                </p>
            </div>
        </div>
        """
    try:
        enviar_correo(usuario.correo, asunto, cuerpo)
    except Exception:
        logger.exception("No se pudo avisar al usuario %s del resultado de su foto",
                         usuario.id)


@bp.route('/admin/fotos')
@login_required
def revision_fotos():
    denegado = _solo_admin()
    if denegado:
        return denegado

    filtro = request.args.get('estado', ESTADO_PENDIENTE)
    if filtro not in (ESTADO_PENDIENTE, ESTADO_APROBADA, ESTADO_RECHAZADA, 'todos'):
        filtro = ESTADO_PENDIENTE

    try:
        pagina = max(int(request.args.get('pagina', 1)), 1)
    except (TypeError, ValueError):
        pagina = 1

    # No se filtra por Usuario.foto: al rechazar se borra la imagen del disco y
    # se pone la columna a NULL, asi que filtrar por foto hacia desaparecer del
    # listado justo lo que el admin necesita poder auditar.
    consulta = Usuario.query.filter(Usuario.foto_estado != ESTADO_SIN_FOTO)
    if filtro != 'todos':
        consulta = consulta.filter(Usuario.foto_estado == filtro)

    # Las más antiguas primero: quien lleva más tiempo esperando su carnet
    # es a quien más urge revisarle la foto.
    consulta = consulta.order_by(Usuario.foto_fecha_subida.asc().nullsfirst())

    # `estado=todos` sin paginar volcaba a todos los usuarios con foto en una
    # sola pantalla, sin tope. Paginado: solo se carga y expone el trozo que
    # el admin está mirando (minimización, Ley 1581).
    paginacion = consulta.paginate(page=pagina, per_page=POR_PAGINA, error_out=False)

    pendientes = Usuario.query.filter(
        Usuario.foto_estado == ESTADO_PENDIENTE).count()

    return render_template('usuarios/revision_fotos.html',
                           usuarios=paginacion.items, filtro=filtro,
                           paginacion=paginacion,
                           pendientes=pendientes,
                           motivos=MOTIVOS_FRECUENTES)


@bp.route('/api/admin/fotos/<int:id>/revisar', methods=['POST'])
@login_required
def api_revisar_foto(id):
    if not current_user.es_admin:
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    datos = request.json or {}
    decision = datos.get('decision')
    if decision not in ('aprobar', 'rechazar'):
        return jsonify({"status": "error", "message": "Decisión no válida"}), 400

    usuario = db.session.get(Usuario, id)
    if usuario is None:
        return jsonify({"status": "error", "message": "El usuario no existe"}), 404
    if not usuario.foto:
        return jsonify({"status": "error",
                        "message": "Ese usuario no tiene foto que revisar"}), 400

    motivo = (sanitize_html(datos.get('motivo')) or '').strip()
    if decision == 'rechazar' and not motivo:
        # Sin motivo, la persona no sabe qué corregir y volverá a subir lo mismo.
        return jsonify({"status": "error",
                        "message": "Indica el motivo del rechazo"}), 400

    if decision == 'aprobar' and usuario.foto_estado == ESTADO_APROBADA:
        # Idempotente: sin esto, volver a pulsar "aprobar" (doble clic, dos
        # pestañas, o llamar la API a mano) reenviaba el correo y añadía otro
        # mensaje automático idéntico en el hilo cada vez.
        restantes = Usuario.query.filter(
            Usuario.foto_estado == ESTADO_PENDIENTE).count()
        return jsonify({
            "status": "success",
            "message": "Esa foto ya estaba aprobada.",
            "pendientes": restantes,
        })

    try:
        ahora = get_colombia_time()
        usuario.foto_revisada_por = current_user.id
        usuario.foto_fecha_revision = ahora

        if decision == 'aprobar':
            usuario.foto_estado = ESTADO_APROBADA
            usuario.foto_motivo = None
            accion = 'Foto de perfil aprobada'
            detalles = f'Se aprobó la foto de {usuario.nombre} ({usuario.correo}).'
        else:
            usuario.foto_estado = ESTADO_RECHAZADA
            usuario.foto_motivo = motivo
            # El carnet se desactiva hasta que suba una foto válida.
            usuario.perfil_completo = False
            accion = 'Foto de perfil rechazada'
            detalles = (f'Se rechazó la foto de {usuario.nombre} '
                        f'({usuario.correo}). Motivo: {motivo}')

            # La foto rechazada se borra: no tiene sentido conservar una imagen
            # que no corresponde a la persona (minimización, Ley 1581).
            ruta = os.path.join(carpeta_fotos(), usuario.foto)
            if os.path.isfile(ruta):
                try:
                    os.remove(ruta)
                except OSError:
                    logger.warning("No se pudo borrar la foto rechazada %s",
                                   usuario.foto)
            usuario.foto = None

        # El motivo queda también en la conversación: el correo se puede
        # perder o ir a spam, el hilo vive dentro del sistema y la persona
        # puede responder ahí mismo si no sabe qué hacer.
        if decision == 'rechazar':
            registrar_mensaje(
                usuario.id, current_user,
                f'Tu foto de perfil no fue aprobada. Motivo: {motivo}\n\n'
                'Sube una foto nueva que cumpla los requisitos. Si tienes algún '
                'problema para hacerlo, respóndeme por aquí.',
                automatico=True)
        else:
            registrar_mensaje(
                usuario.id, current_user,
                'Tu foto de perfil fue aprobada. Tu carnet digital ya está activo.',
                automatico=True)

        db.session.add(Auditoria(
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            tabla_afectada='usuarios',
            registro_id=usuario.id,
            accion=accion,
            autorizado_por=current_user.nombre,
            motivo=motivo or 'Revisión de foto de perfil',
            detalles=detalles,
            fecha=ahora,
        ))
        db.session.commit()

        _avisar_por_correo(usuario, decision == 'aprobar', motivo)
        logger.info("Foto del usuario %s: %s", usuario.id, accion)

        restantes = Usuario.query.filter(
            Usuario.foto_estado == ESTADO_PENDIENTE).count()
        return jsonify({
            "status": "success",
            "message": ('Foto aprobada. El carnet quedó activo.'
                        if decision == 'aprobar'
                        else 'Foto rechazada. Se avisó a la persona para que suba otra.'),
            "pendientes": restantes,
        })
    except Exception:
        db.session.rollback()
        logger.exception("Error revisando la foto del usuario %s", id)
        return jsonify({"status": "error",
                        "message": "No se pudo registrar la revisión"}), 500


@bp.app_context_processor
def inyectar_fotos_pendientes():
    """Contador para el menú lateral, solo para administradores."""
    if not (current_user.is_authenticated and current_user.es_admin):
        return {'fotos_pendientes': 0}
    try:
        return {'fotos_pendientes': Usuario.query.filter(
            Usuario.foto_estado == ESTADO_PENDIENTE).count()}
    except Exception:
        # Si la columna aún no existe (base sin migrar), no romper toda la app.
        return {'fotos_pendientes': 0}
