from flask import Blueprint

bp = Blueprint('equipos', __name__, url_prefix='/equipos')

from . import routes
