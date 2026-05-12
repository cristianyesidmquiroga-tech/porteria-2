from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...models.entidades import Equipo
from ... import db
from . import bp

@bp.route('/add', methods=['POST'])
@login_required
def add_device():
    nombre = request.form.get('nombre')
    serial = request.form.get('serial')
    tipo = request.form.get('tipo')

    new_device = Equipo(
        nombre=nombre,
        serial=serial,
        tipo=tipo,
        usuario_id=current_user.id)
    db.session.add(new_device)
    db.session.commit()

    msg = 'Dispositivo registrado correctamente.'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": msg, "reload": True}
    flash(msg, 'success')
    return redirect(url_for('usuarios.profile'))

@bp.route('/delete/<int:id>')
@login_required
def delete_device(id):
    equipo = Equipo.query.get_or_404(id)
    if equipo.usuario_id != current_user.id:
        flash('No tienes permiso para eliminar este dispositivo.', 'danger')
        return redirect(url_for('usuarios.profile'))

    db.session.delete(equipo)
    db.session.commit()
    flash('Dispositivo eliminado.', 'info')
    return redirect(url_for('usuarios.profile'))
