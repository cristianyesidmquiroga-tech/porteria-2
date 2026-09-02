from flask import Blueprint

bp = Blueprint('coordinacion', __name__, url_prefix='/coordinacion')
coordinacion_bp = bp

from . import routes
