from app.utils import get_colombia_time
from .. import db


class Visitante(db.Model):
    __tablename__ = 'visitantes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(100), unique=True, nullable=False)
    motivo = db.Column(db.Text, nullable=True)
    qr_code = db.Column(db.String(255), unique=True, nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(
        db.DateTime,
        default=get_colombia_time)


class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=True)  # 'SENA' or 'Externo'
    propietario = db.Column(db.String(100), nullable=True)
    motivo = db.Column(db.Text, nullable=True)  # Why is this vehicle here?
    qr_code = db.Column(db.String(255), unique=True, nullable=True)
    activo = db.Column(db.Boolean, default=True)


class Equipo(db.Model):
    __tablename__ = 'equipos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    serial = db.Column(db.String(100), unique=True, nullable=True)
    # e.g., 'Portátil', 'Celular'
    tipo = db.Column(db.String(50), nullable=True)
    estado = db.Column(
        db.String(20),
        default='Afuera')  # 'Adentro' or 'Afuera'
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=True)


class ObjetoExterno(db.Model):
    __tablename__ = 'objetos_externos'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False)

