from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...models.entidades import Equipo
from ...utils.security import sanitize_html
from ... import db
from . import bp

TIPOS_VALIDOS = {'Portátil', 'Portatil', 'Computador', 'Tablet', 'Celular', 'Otro'}
MAX_EQUIPOS_POR_USUARIO = 5


def _responder(ok, mensaje, categoria):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if ok:
            return {"status": "success", "message": mensaje, "reload": True}
        return {"status": "error", "message": mensaje}, 400
    flash(mensaje, categoria)
    return redirect(url_for('usuarios.profile'))


@bp.route('/add', methods=['POST'])
@login_required
def add_device():
    if not current_user.puede_registrar_equipos:
        return _responder(False, 'Tu perfil no puede registrar equipos.', 'danger')

    # Estos valores se muestran despues en el escaner de porteria, asi que se
    # limpian y acotan aqui, en el servidor.
    nombre = sanitize_html(request.form.get('nombre', '')).strip()
    serial = sanitize_html(request.form.get('serial', '')).strip()
    tipo = sanitize_html(request.form.get('tipo', '')).strip()

    if not nombre:
        return _responder(False, 'El nombre del equipo es obligatorio.', 'warning')
    if len(nombre) > 100:
        return _responder(False, 'El nombre del equipo es demasiado largo.', 'warning')
    if serial and len(serial) > 100:
        return _responder(False, 'El serial es demasiado largo.', 'warning')
    if tipo and tipo not in TIPOS_VALIDOS:
        return _responder(False, 'Tipo de equipo no valido.', 'warning')

    registrados = Equipo.query.filter_by(usuario_id=current_user.id).count()
    if registrados >= MAX_EQUIPOS_POR_USUARIO:
        return _responder(
            False,
            f'Solo puedes registrar hasta {MAX_EQUIPOS_POR_USUARIO} equipos.',
            'warning')

    if serial and Equipo.query.filter_by(serial=serial).first():
        return _responder(False, 'Ya existe un equipo registrado con ese serial.',
                          'warning')

    db.session.add(Equipo(
        nombre=nombre,
        serial=serial or None,
        tipo=tipo or 'Otro',
        usuario_id=current_user.id,
    ))
    db.session.commit()
    return _responder(True, 'Dispositivo registrado correctamente.', 'success')


# Antes era una ruta GET: bastaba con que la victima cargara una imagen
# apuntando a esta URL para borrarle el equipo. Ahora exige POST, que si pasa
# por la proteccion CSRF.
@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_device(id):
    equipo = db.session.get(Equipo, id)
    if equipo is None:
        return _responder(False, 'El dispositivo no existe.', 'warning')

    if equipo.usuario_id != current_user.id:
        return _responder(False, 'No tienes permiso para eliminar este dispositivo.',
                          'danger')

    db.session.delete(equipo)
    db.session.commit()
    return _responder(True, 'Dispositivo eliminado.', 'info')
