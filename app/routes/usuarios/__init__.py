from flask import Blueprint

bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

from . import (perfil, asistencia, admin_usuarios,  # noqa: F401
               revision_fotos, mensajes, ayuda, tutorial, fichas, fotos)
