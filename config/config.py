import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # SECRET_KEY fija para evitar errores de CSRF al reiniciar el servidor
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sena_carnet_secure_key_2024_ag_v1'
    database_url = os.environ.get('DATABASE_URL')

    # Convertir URL de estilo antiguo a formato compatible con SQLAlchemy
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url or (
        'sqlite:///' + os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'instance', 'carnets.sqlite')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
