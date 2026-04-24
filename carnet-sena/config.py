import os
import secrets
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # SECRET_KEY fija para evitar errores de CSRF al reiniciar el servidor
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sena_carnet_secure_key_2024_ag_v1'
    # Corrected path for SQLite in the instance folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'carnets.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
