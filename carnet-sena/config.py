import os
import secrets
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # SECRET_KEY fija para evitar errores de CSRF al reiniciar el servidor
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sena_carnet_secure_key_2024_ag_v1'
    database_url = os.environ.get('DATABASE_URL')
    
    # FORZAR LA URL CORRECTA SI COOLIFY INYECTA LA ANTIGUA
    if database_url and "sqj21c1qvz5jsuj0rs10pdx0" in database_url:
        database_url = "postgresql://postgres:123postgres@lsdeklphbrt9022pgozvpqks:5432/postgres?sslmode=require"
    elif database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'carnets.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
