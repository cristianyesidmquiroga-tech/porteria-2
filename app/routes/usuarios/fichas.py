"""Administracion de fichas de formacion.

El programa y la fecha de finalizacion se registran aqui una sola vez por
ficha; los aprendices los heredan al elegir su ficha en el perfil. Es una
pantalla solo para administradores: quien pueda editar una ficha cambia de
golpe lo que sale impreso en el carnet de todos sus aprendices.
"""

import re
from datetime import datetime

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from ... import db
from ...models.fichas import Ficha
from ...models.usuarios import Usuario
from ...utils.security import sanitize_html
from . import bp

# El numero de ficha del SENA es una secuencia de digitos. Se valida para que
# no entren nombres ni codigos inventados que despues no cuadran con nada.
_NUMERO_VALIDO = re.compile(r'^\d{4,12}$')


def _solo_admin():
    if not current_user.es_admin:
        flash('Acceso denegado. Área exclusiva para administradores.', 'danger')
        return redirect(url_for('main.index'))
    return None


def _leer_formulario():
    """Extrae y valida los campos del formulario. Devuelve (datos, error)."""
    numero = sanitize_html(request.form.get('numero') or '').strip()
    programa = sanitize_html(request.form.get('programa') or '').strip()
    fecha_texto = (request.form.get('fecha_finalizacion') or '').strip()

    if not _NUMERO_VALIDO.match(numero):
        return None, 'El número de ficha debe tener entre 4 y 12 dígitos.'
    if not programa:
        return None, 'El nombre del programa de formación es obligatorio.'
    if len(programa) > 150:
        return None, 'El nombre del programa no puede superar los 150 caracteres.'

    fecha = None
    if fecha_texto:
        try:
            # El input type="date" siempre manda aaaa-mm-dd. Se guarda como
            # fecha suelta, sin hora: no hay conversion de zona horaria que
            # pueda correrla un dia.
            fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
        except ValueError:
            return None, 'La fecha de finalización no es válida.'

    return {'numero': numero, 'programa': programa, 'fecha': fecha}, None


@bp.route('/admin/fichas')
@login_required
def admin_fichas():
    negado = _solo_admin()
    if negado:
        return negado

    fichas = Ficha.query.order_by(Ficha.activa.desc(), Ficha.numero).all()
    # Cuantos aprendices cuelgan de cada ficha: hace visible el alcance real
    # de editarla antes de tocarla.
    conteo = dict(
        db.session.query(Usuario.ficha_id, db.func.count(Usuario.id))
        .filter(Usuario.ficha_id.isnot(None))
        .group_by(Usuario.ficha_id).all()
    )
    return render_template('usuarios/fichas.html', fichas=fichas, conteo=conteo)


@bp.route('/admin/fichas/crear', methods=['POST'])
@login_required
def crear_ficha():
    negado = _solo_admin()
    if negado:
        return negado

    datos, error = _leer_formulario()
    if error:
        flash(error, 'danger')
        return redirect(url_for('usuarios.admin_fichas'))

    if Ficha.query.filter_by(numero=datos['numero']).first():
        flash(f"La ficha {datos['numero']} ya está registrada.", 'warning')
        return redirect(url_for('usuarios.admin_fichas'))

    db.session.add(Ficha(numero=datos['numero'], programa=datos['programa'],
                         fecha_finalizacion=datos['fecha']))
    db.session.commit()
    flash(f"Ficha {datos['numero']} creada.", 'success')
    return redirect(url_for('usuarios.admin_fichas'))


@bp.route('/admin/fichas/<int:ficha_id>/editar', methods=['POST'])
@login_required
def editar_ficha(ficha_id):
    negado = _solo_admin()
    if negado:
        return negado

    ficha = db.session.get(Ficha, ficha_id)
    if not ficha:
        flash('Esa ficha ya no existe.', 'warning')
        return redirect(url_for('usuarios.admin_fichas'))

    datos, error = _leer_formulario()
    if error:
        flash(error, 'danger')
        return redirect(url_for('usuarios.admin_fichas'))

    repetida = Ficha.query.filter(Ficha.numero == datos['numero'],
                                  Ficha.id != ficha.id).first()
    if repetida:
        flash(f"Ya existe otra ficha con el número {datos['numero']}.", 'warning')
        return redirect(url_for('usuarios.admin_fichas'))

    ficha.numero = datos['numero']
    ficha.programa = datos['programa']
    ficha.fecha_finalizacion = datos['fecha']
    db.session.commit()
    flash(f'Ficha {ficha.numero} actualizada.', 'success')
    return redirect(url_for('usuarios.admin_fichas'))


@bp.route('/admin/fichas/<int:ficha_id>/archivar', methods=['POST'])
@login_required
def archivar_ficha(ficha_id):
    """Activa o archiva la ficha.

    No se borra nunca: sus aprendices la referencian y su carnet dejaria de
    tener programa y fecha de un dia para otro.
    """
    negado = _solo_admin()
    if negado:
        return negado

    ficha = db.session.get(Ficha, ficha_id)
    if not ficha:
        flash('Esa ficha ya no existe.', 'warning')
        return redirect(url_for('usuarios.admin_fichas'))

    ficha.activa = not ficha.activa
    db.session.commit()
    flash(f"Ficha {ficha.numero} {'reactivada' if ficha.activa else 'archivada'}.",
          'success')
    return redirect(url_for('usuarios.admin_fichas'))
