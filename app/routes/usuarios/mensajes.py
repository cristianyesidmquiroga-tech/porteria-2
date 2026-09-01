"""Conversación entre una persona y los administradores.

Sirve para dos cosas que antes no tenían canal:
  - que el administrador explique qué le falta o por qué se rechazó algo,
  - y que la persona pueda preguntar cuando no sabe qué hacer.

Sin esto, quien queda bloqueado sin carnet no tiene a quién escribir desde el
propio sistema.
"""
import logging

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ... import db
from ...models.mensajes import (
    Mensaje,
    hilos_con_respuesta_pendiente,
    registrar_mensaje,
    sin_leer_para_usuario,
)
from ...models.usuarios import Usuario
from ...utils.security import sanitize_html
from . import bp

logger = logging.getLogger(__name__)

LARGO_MAXIMO_MENSAJE = 2000


def _texto_valido(bruto):
    """Limpia y valida el texto. Devuelve (texto, error_o_None)."""
    texto = (sanitize_html(bruto) or '').strip()
    if not texto:
        return '', 'Escribe un mensaje antes de enviarlo.'
    if len(texto) > LARGO_MAXIMO_MENSAJE:
        return '', f'El mensaje no puede superar los {LARGO_MAXIMO_MENSAJE} caracteres.'
    return texto, None


@bp.route('/mensajes')
@login_required
def mis_mensajes():
    """Hilo de la persona que ha iniciado sesión."""
    mensajes = Mensaje.query.filter_by(usuario_id=current_user.id) \
        .order_by(Mensaje.fecha.asc()).all()

    # Al abrir el hilo se dan por leídos los mensajes del administrador.
    pendientes = [m for m in mensajes
                  if m.autor_id != current_user.id and not m.leido]
    if pendientes:
        for mensaje in pendientes:
            mensaje.leido = True
        db.session.commit()

    return render_template('usuarios/mensajes.html', mensajes=mensajes,
                           persona=current_user, es_vista_admin=False)


@bp.route('/mensajes/enviar', methods=['POST'])
@login_required
def enviar_mensaje():
    """La persona escribe a los administradores."""
    texto, error = _texto_valido(request.form.get('texto'))
    if error:
        flash(error, 'warning')
        return redirect(url_for('usuarios.mis_mensajes'))

    registrar_mensaje(current_user.id, current_user, texto)
    db.session.commit()
    flash('Mensaje enviado. Un administrador te responderá por aquí.', 'success')
    return redirect(url_for('usuarios.mis_mensajes'))


@bp.route('/admin/mensajes')
@login_required
def admin_mensajes():
    """Bandeja del administrador: un hilo por persona."""
    if not current_user.puede_asesorar:
        flash('Acceso denegado. Área exclusiva para administradores.', 'danger')
        return redirect(url_for('main.index'))

    # Se listan las personas que tienen conversación, con lo último escrito y
    # cuántos mensajes suyos siguen sin leer.
    filas = []
    ids = [fila[0] for fila in db.session.query(Mensaje.usuario_id).distinct().all()]
    for usuario_id in ids:
        persona = db.session.get(Usuario, usuario_id)
        if persona is None:
            continue
        ultimo = Mensaje.query.filter_by(usuario_id=usuario_id) \
            .order_by(Mensaje.fecha.desc()).first()
        sin_leer = Mensaje.query.filter(
            Mensaje.usuario_id == usuario_id,
            Mensaje.autor_id == usuario_id,
            Mensaje.leido.is_(False)).count()
        filas.append({'persona': persona, 'ultimo': ultimo, 'sin_leer': sin_leer})

    # Primero quien espera respuesta, y dentro de eso lo más reciente.
    filas.sort(key=lambda f: (-f['sin_leer'],
                              -(f['ultimo'].fecha.timestamp() if f['ultimo'] and f['ultimo'].fecha else 0)))

    return render_template('usuarios/admin_mensajes.html', filas=filas)


@bp.route('/admin/mensajes/<int:id>')
@login_required
def admin_hilo(id):
    if not current_user.puede_asesorar:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))

    persona = db.session.get(Usuario, id)
    if persona is None:
        flash('Esa persona no existe.', 'warning')
        return redirect(url_for('usuarios.admin_mensajes'))

    mensajes = Mensaje.query.filter_by(usuario_id=id) \
        .order_by(Mensaje.fecha.asc()).all()

    pendientes = [m for m in mensajes if m.autor_id == id and not m.leido]
    if pendientes:
        for mensaje in pendientes:
            mensaje.leido = True
        db.session.commit()

    return render_template('usuarios/mensajes.html', mensajes=mensajes,
                           persona=persona, es_vista_admin=True)


@bp.route('/api/admin/mensajes/<int:id>', methods=['POST'])
@login_required
def api_responder(id):
    """El administrador escribe a una persona."""
    if not current_user.puede_asesorar:
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    persona = db.session.get(Usuario, id)
    if persona is None:
        return jsonify({"status": "error", "message": "Esa persona no existe"}), 404

    datos = request.json or {}
    texto, error = _texto_valido(datos.get('texto'))
    if error:
        return jsonify({"status": "error", "message": error}), 400

    registrar_mensaje(persona.id, current_user, texto)
    db.session.commit()
    logger.info("Administrador %s escribió al usuario %s", current_user.id, persona.id)

    return jsonify({"status": "success",
                    "message": f'Mensaje enviado a {persona.nombre}.'})


@bp.app_context_processor
def inyectar_mensajes():
    """Contadores para el menú lateral."""
    vacio = {'mensajes_sin_leer': 0, 'hilos_pendientes': 0}
    if not current_user.is_authenticated:
        return vacio
    try:
        datos = {'mensajes_sin_leer': sin_leer_para_usuario(current_user),
                 'hilos_pendientes': 0}
        if current_user.puede_asesorar:
            datos['hilos_pendientes'] = hilos_con_respuesta_pendiente()
        return datos
    except Exception:
        # Si la tabla aún no existe (base sin migrar), no romper toda la app.
        return vacio
