from flask import Blueprint

porteria_bp = Blueprint('porteria', __name__, url_prefix='/porteria')

# Importamos las rutas para que se registren en el blueprint
from . import dashboard
from . import scanner
from . import pases
from . import reportes

