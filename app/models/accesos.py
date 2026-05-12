from app.utils import get_colombia_time
from .. import db



class PuntoAcceso(db.Model):
    __tablename__ = 'puntos_acceso'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Por ejemplo: 'Entrada Principal', 'Salida Peatonal'
    tipo = db.Column(db.String(50), nullable=False)
    accesos = db.relationship('Acceso', backref='punto', lazy=True)


class Acceso(db.Model):
    __tablename__ = 'accesos'
    id = db.Column(db.Integer, primary_key=True)
    punto_id = db.Column(
        db.Integer,
        db.ForeignKey('puntos_acceso.id'),
        nullable=False)
    carnet_id = db.Column(
        db.Integer,
        db.ForeignKey('carnets.id'),
        nullable=True)  # Opcional para visitantes o pases manuales
    # ID de la entidad específica (Usuario, Visitante, etc.)
    referencia_id = db.Column(db.Integer, nullable=False)
    # Define si es 'Usuario', 'Visitante', etc.
    tipo_referencia = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'Entrada' o 'Salida'
    fecha = db.Column(db.DateTime, default=get_colombia_time)
    equipos_str = db.Column(db.String(255), nullable=True)


class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    tabla_afectada = db.Column(db.String(100), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    accion = db.Column(db.String(255), nullable=False)
    # Nuevos campos solicitados
    autorizado_por = db.Column(db.String(100), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    detalles = db.Column(db.Text, nullable=True) # Para guardar qué cambió exactamente
    fecha = db.Column(db.DateTime, default=get_colombia_time)

