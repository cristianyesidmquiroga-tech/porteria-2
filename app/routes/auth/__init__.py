from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

# El chequeo de sesion unica y verificacion de correo se registra en
# create_app(), no aqui: colgarlo del blueprint hacia que dejara de aplicarse
# en toda la aplicacion si alguien dejaba de importar este modulo.

from . import (login, registro, verificacion, logout, recuperacion,  # noqa: E402,F401
               desafio)
