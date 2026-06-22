from flask import Blueprint

coordinacion_bp = Blueprint('coordinacion', __name__, url_prefix='/coordinacion')

from . import routes
