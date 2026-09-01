"""Entrega de las fotos de perfil, con sesion y permiso comprobados.

Sustituye a servirlas desde `static/`, donde cualquiera podia descargarlas sin
cuenta recorriendo los ids. Ver `app/utils/fotos.py` para el porque.
"""
import os

from flask import abort, send_file
from flask_login import current_user, login_required

from . import bp
from app.utils.fotos import puede_ver_la_foto, ruta_de_foto
from app.models.usuarios import Usuario


@bp.route('/foto/<int:usuario_id>')
@login_required
def foto_perfil(usuario_id):
    """Devuelve la foto de un usuario si quien la pide tiene por que verla."""
    if not puede_ver_la_foto(current_user, usuario_id):
        # 404 y no 403: un 403 confirmaria que esa persona existe y tiene foto.
        abort(404)

    usuario = Usuario.query.get(usuario_id)
    if usuario is None:
        abort(404)

    ruta = ruta_de_foto(usuario.foto)
    if ruta is None:
        # La columna puede apuntar a un archivo ya borrado; quien llama debe
        # haber pedido el avatar del cargo en ese caso.
        abort(404)

    respuesta = send_file(ruta, mimetype='image/jpeg',
                          last_modified=os.path.getmtime(ruta))
    # Privada: puede quedar en el navegador de quien la vio, nunca en una cache
    # compartida por la que pasen varias personas.
    respuesta.headers['Cache-Control'] = 'private, max-age=300'
    return respuesta
