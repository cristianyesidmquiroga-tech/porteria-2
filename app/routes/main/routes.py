from flask import redirect, url_for, render_template
from flask_login import current_user
from . import bp


@bp.route('/')
def index():
    # Antes esta ruta cerraba la sesion de cualquier usuario autenticado, asi
    # que entrar a la raiz (o hacer clic en el logo) desconectaba al usuario.
    if current_user.is_authenticated:
        if current_user.puede_operar_porteria:
            return redirect(url_for('porteria.dashboard'))
        return redirect(url_for('usuarios.profile'))
    return redirect(url_for('auth.login'))


@bp.route('/salud')
def salud():
    """Sonda de salud para el healthcheck del contenedor. Sin autenticacion."""
    return {"estado": "ok"}, 200


@bp.route('/politica-privacidad')
def politica_privacidad():
    return render_template('main/politica_privacidad.html')
