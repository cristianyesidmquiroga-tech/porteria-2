from flask import Blueprint
from ...utils.security import check_security_and_verification

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def check_security():
    return check_security_and_verification()

# Importamos las rutas para que se registren en el blueprint
from . import login, registro, verificacion, logout, recuperacion
